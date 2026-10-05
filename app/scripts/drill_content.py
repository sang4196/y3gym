"""Synthetic content only, invoked by the one-shot rehearsal runner."""
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from PIL import Image as PillowImage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from wagtail.images import get_image_model
from wagtail.models import Revision
from content.models import SiteContent, Branch, BranchPhoto, Trainer, TrainerCareer, Post, PostImageUse, Popup
from content.operators import configure_operator
from content.publication import public_snapshot, public_images
from content.post_publication import post_snapshot
from content.popup_publication import popups_snapshot
from content.locking import content_transaction
from content.views import private_file
from scripts.restore_drill import inventory

T=datetime(2030,1,1,tzinfo=dt_timezone.utc)


def seed():
    assert not SiteContent.objects.exists() and not Post.objects.exists()
    user=get_user_model().objects.create_user(username='TEST-drill-editor',password=None,is_staff=True)
    assert not user.has_usable_password() and not user.is_superuser
    collection=configure_operator(user)
    images=[]
    for name,color in [('site','green'),('shared','orange'),('draft','purple'),('past','blue'),('popup','red')]:
        file=BytesIO();PillowImage.new('RGB',(64,48),color).save(file,'PNG')
        images.append(get_image_model().objects.create(title='TEST '+name,collection=collection,
                      file=SimpleUploadedFile('TEST-'+name+'.png',file.getvalue(),content_type='image/png')))
    site,shared,draft,past,popup=images
    SiteContent(brand_name='TEST RESTORE ONLY',hero_title='TEST synthetic',hero_image=site).save()
    public=Branch(name='TEST PUBLIC',address='TEST ADDRESS',phone='000-0000-0000',is_public=True);public.save()
    hidden=Branch(name='TEST HIDDEN',address='TEST hidden',phone='000-0000-0000');hidden.save()
    BranchPhoto.objects.create(branch=public,image=shared,caption='TEST shared facility',alt='TEST orange')
    trainer=Trainer(branch=public,name='TEST trainer',short_intro='TEST intro',profile_image=site,is_public=True);trainer.save()
    trainer.careers.add(TrainerCareer(category='education',text='TEST education',sort_order=0));trainer.save()
    Trainer(branch=hidden,name='TEST hidden trainer',short_intro='TEST hidden',profile_image=site,is_public=True).save()
    post=Post(title='TEST PAST',body='<p>TEST PAST BODY</p>',cover_image=past);post.save()
    revision=post.save_revision(user=user);post.publish(revision,user=user)
    post.title='TEST LIVE';post.body=f'<p>TEST LIVE <b>Bold</b></p><embed embedtype="image" id="{shared.pk}" format="fullwidth" alt="TEST shared"/>';post.cover_image=shared;post.save()
    revision=post.save_revision(user=user);post.publish(revision,user=user)
    post.title='TEST DRAFT';post.body='<p>TEST PRIVATE DRAFT</p>';post.cover_image=draft;post.save();post.save_revision(user=user)
    Popup(post=post,title='TEST POPUP',message='TEST time window',image=popup,enabled=True,starts_at=T,ends_at=T+timedelta(hours=1)).save()


def snapshot():
    with patch('django.utils.timezone.now',return_value=T+timedelta(minutes=1)),content_transaction(read=True):
        public=public_snapshot();detail=post_snapshot(Post.objects.get().pk)
        candidates=popups_snapshot()
        rows={model.__name__:list(model.objects.order_by('pk').values()) for model in [SiteContent,Branch,BranchPhoto,Trainer,TrainerCareer,Post,PostImageUse,Popup]}
        rows['Revision']=list(Revision.objects.filter(content_type__app_label='content',content_type__model='post').order_by('pk').values('pk','object_id','content'))
    return {'public':public,'post':detail,'popup':candidates,'rows_hash':hashlib.sha256(json.dumps(rows,default=str,sort_keys=True).encode()).hexdigest(),
            'media':inventory(Path(settings.MEDIA_ROOT))}


def verify():
    checks=[]
    client=Client();post=Post.objects.get();images={i.title:i for i in get_image_model().objects.all()}
    with patch('django.utils.timezone.now',return_value=T+timedelta(minutes=1)):
        for path in ['/', '/branches/', '/trainers/', '/posts/', post.get_absolute_url()]:
            response=client.get(path);assert response.status_code==200
            assert b'TEST DRAFT' not in response.content and b'TEST PRIVATE DRAFT' not in response.content
            assert b'TEST HIDDEN' not in response.content
        dto=client.get(f'/api/v1/posts/{post.pk}/').json()['data'];assert dto['title']=='TEST LIVE'
        assert post.get_latest_revision_as_object().title=='TEST DRAFT'
        assert post.revisions.count()==3 and post.live_revision_id!=post.latest_revision_id
        assert post.public_image_uses.count()==1
        checks.append('restored HTML/JSON/live revision/draft/history/relations')
        for title,expected in [('TEST shared',200),('TEST draft',404),('TEST past',404),('TEST popup',200)]:
            response=client.get(f'/images/display/{images[title].pk}/');assert response.status_code==expected
            if response.streaming:b''.join(response.streaming_content);response.close()
        user=get_user_model().objects.get(username='TEST-drill-editor');assert not user.has_usable_password()
        request=RequestFactory().get('/admin/preview/');request.user=user
        preview=post.get_latest_revision_as_object().serve_preview(request,'')
        assert preview.status_code==200 and b'TEST DRAFT' in preview.content and b'cms-files' in preview.content
        assert client.get(images['TEST draft'].file.url).status_code==403
        protected=private_file(request,images['TEST draft'].file.name);assert protected.status_code==200
        b''.join(protected.streaming_content);protected.close()
        checks.append('draft/past assets private; shared/popup public; authenticated preview and original')
    for instant,count in [(T-timedelta(microseconds=1),0),(T,1),(T+timedelta(hours=1),0)]:
        with patch('django.utils.timezone.now',return_value=instant):
            assert len(client.get('/api/v1/popups/active/').json()['items'])==count
            response=client.get(f'/images/display/{images["TEST popup"].pk}/');assert response.status_code==(200 if count else 404)
            if response.streaming:b''.join(response.streaming_content);response.close()
    checks.append('fixed popup start/end boundary and media access')
    # Sharing survives one removed placement, then closes at last public reference.
    BranchPhoto.objects.all().delete()
    with content_transaction(read=True): assert public_images().filter(pk=images['TEST shared'].pk).exists()
    post.unpublish(user=user)
    assert client.get(f'/images/display/{images["TEST shared"].pk}/').status_code==404
    assert client.get(post.get_absolute_url()).status_code==404
    checks.append('shared image survives one reference removal and closes at last reference')
    # Historical content becomes a NEW draft, never a direct old-version publish.
    old=post.revisions.order_by('pk').first();post.refresh_from_db()
    restored=post.with_content_json(old.content);restored.save();new=restored.save_revision(user=user)
    post.refresh_from_db();assert new.pk!=old.pk and not post.live
    assert post.get_latest_revision_as_object().title=='TEST PAST'
    assert client.get(f'/images/display/{images["TEST past"].pk}/').status_code==404
    checks.append('historical revision -> new draft without publication')
    return checks


def run():
    assert settings.SETTINGS_MODULE=='config.settings.rehearsal'
    action=os.environ['Y3GYM_DRILL_ACTION'];side=os.environ['Y3GYM_DRILL_SIDE']
    if action=='seed':
        assert side=='src';seed();print('Synthetic content seeded; unusable-password operator only')
    elif action=='snapshot':
        data=snapshot()
        with (Path(settings.MEDIA_ROOT).parent/(side+'-snapshot.json')).open('x') as f:json.dump(data,f,default=str,indent=2)
        print('Public projection, content hashes and media manifest captured')
    elif action=='verify':
        assert side=='dst';checks=verify()
        with (Path(settings.MEDIA_ROOT).parent/'verification.json').open('x') as f:json.dump(checks,f,indent=2)
        print('PASS:',len(checks),'restored content scenarios')
    else:raise ValueError('Unknown rehearsal action')
