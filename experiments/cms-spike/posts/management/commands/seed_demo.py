import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from wagtail.images import get_image_model
from posts.models import Post
from posts.test_support import configure_editor, test_png


class Command(BaseCommand):
    help = "Create clearly synthetic demo posts/images once; preserve prior demo state."

    def handle(self, **options):
        manifest = settings.RUNTIME / "demo.json"
        if manifest.exists():
            data = json.loads(manifest.read_text())
            if not all(Post.objects.filter(pk=pk).exists() for pk in data["posts"].values()):
                raise CommandError("Existing demo manifest and DB differ. No reset performed.")
            self.stdout.write("Existing demo preserved: " + json.dumps(data))
            return
        owner, created = get_user_model().objects.get_or_create(username="spike-fixture-owner")
        if not created:
            raise CommandError("Fixture owner already exists without manifest; inspect manually. No overwrite.")
        owner.set_unusable_password()
        owner.save()
        collection = configure_editor(owner)
        images = []
        fixtures = settings.RUNTIME / "fixtures"
        fixtures.mkdir(exist_ok=True)
        for name, color in [("public-cover.png", "red"), ("public-body.png", "blue"), ("draft-cover.png", "green"), ("draft-body.png", "purple")]:
            file = test_png(name, color)
            fixture_path = fixtures / name
            if not fixture_path.exists():
                with fixture_path.open("xb") as stream:
                    stream.write(file.read())
                file.seek(0)
            images.append(get_image_model().objects.create(title="SPIKE TEST " + name, file=file, collection=collection, uploaded_by_user=owner))
        def body(image, text):
            return f'<h2>{text}</h2><p><b>TEST ONLY</b> <a href="https://example.com/">Test link</a></p><embed embedtype="image" id="{image.pk}" format="fullwidth" alt="TEST rectangle"/>'
        a = Post.objects.create(title="SPIKE PUBLIC A", category="notice", body=body(images[1], "PUBLIC BODY"), cover_image=images[0], live=False)
        a.save_revision(user=owner).publish(user=owner)
        a.refresh_from_db()
        a.title, a.body, a.cover_image = "SPIKE DRAFT A", body(images[3], "DRAFT BODY"), images[2]
        a.save_revision(user=owner)
        b = Post.objects.create(title="SPIKE PUBLIC B", category="event", body=body(images[1], "SHARED BODY"), live=False)
        b.save_revision(user=owner).publish(user=owner)
        data = {"posts": {"a": a.pk, "b": b.pk}, "images": {image.title: image.pk for image in images}}
        with manifest.open("x") as stream:
            json.dump(data, stream, indent=2)
        self.stdout.write("Synthetic demo created: " + json.dumps(data))
