from django import forms
from wagtail.admin.forms import WagtailAdminModelForm


class PostForm(WagtailAdminModelForm):
    def clean(self):
        from wagtail.images import get_image_model
        from wagtail.images.permissions import permission_policy
        from .models import Post
        from .publication import image_ids
        data = super().clean()
        candidate = Post(body=data.get("body", ""), cover_image=data.get("cover_image"))
        for image_id in image_ids(candidate):
            image = get_image_model().objects.filter(pk=image_id).first()
            if image is None or not permission_policy.user_has_any_permission_for_instance(self.for_user, ["choose", "change"], image):
                raise forms.ValidationError("Every selected image requires collection permission.")
            if not image.file.storage.exists(image.file.name):
                raise forms.ValidationError("A selected image file is missing; restore or select a new asset.")
        return data
