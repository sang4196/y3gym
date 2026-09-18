"""Synthetic fixtures shared by request tests and the manual demo command."""
from io import BytesIO
from PIL import Image as PillowImage, ImageDraw
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.models import Collection, GroupCollectionPermission


def test_png(name, color):
    output = BytesIO()
    image = PillowImage.new("RGB", (960, 720), color)
    ImageDraw.Draw(image).text((20, 20), "SPIKE-01 TEST ONLY", fill="white")
    image.save(output, "PNG")
    return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")


def configure_editor(user):
    group, _ = Group.objects.get_or_create(name="SPIKE-01 content editor")
    group.permissions.add(Permission.objects.get(content_type__app_label="wagtailadmin", codename="access_admin"))
    for code in ["add_post", "change_post", "view_post", "publish_post"]:
        group.permissions.add(Permission.objects.get(content_type__app_label="posts", codename=code))
    root = Collection.get_first_root_node()
    collection = root.get_children().filter(name="SPIKE-01 test images").first()
    if collection is None:
        collection = root.add_child(name="SPIKE-01 test images")
    for code in ["add_image", "change_image", "choose_image"]:
        GroupCollectionPermission.objects.get_or_create(
            group=group, collection=collection,
            permission=Permission.objects.get(content_type__app_label="wagtailimages", codename=code),
        )
    user.groups.add(group)
    return collection
