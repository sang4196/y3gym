from django.contrib.auth.models import Group, Permission
from wagtail.models import Collection, GroupCollectionPermission

def configure_operator(user):
    group, _ = Group.objects.get_or_create(name='홈페이지 운영자')
    wanted = Permission.objects.filter(content_type__app_label='content', codename__in=['add_sitecontent','change_sitecontent','view_sitecontent','add_branch','change_branch','view_branch'])
    group.permissions.set(list(wanted) + [Permission.objects.get(content_type__app_label='wagtailadmin',codename='access_admin')])
    root = Collection.get_first_root_node()
    collection = root.get_children().filter(name='홈페이지 사진').first()
    if collection is None: collection = root.add_child(name='홈페이지 사진')
    for code in ['add_image','change_image','choose_image']:
        GroupCollectionPermission.objects.get_or_create(group=group,collection=collection,permission=Permission.objects.get(content_type__app_label='wagtailimages',codename=code))
    user.groups.add(group)
    return collection
