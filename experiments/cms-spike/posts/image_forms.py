from django import forms
from wagtail.images.forms import BaseImageForm


class ImmutableImageForm(BaseImageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and "file" in self.fields:
            self.fields["file"].disabled = True
            self.fields["file"].help_text = "Upload a new image and change the post reference. Existing files cannot be replaced."

    def clean(self):
        data = super().clean()
        if self.instance.pk and self.add_prefix("file") in self.files:
            raise forms.ValidationError("Existing image files cannot be replaced; upload a new asset.")
        return data
