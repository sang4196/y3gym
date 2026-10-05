"""Post-only composition UI; the standard content-state converter is unchanged."""
from django.forms import Media
from django.utils.functional import cached_property
from wagtail.admin.rich_text.editors.draftail import DraftailRichTextArea


class PostRichTextArea(DraftailRichTextArea):
    template_name = "content/widgets/composer.html"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("features", ["h2", "bold", "italic", "ol", "ul", "link", "image"])
        super().__init__(*args, **kwargs)
        self.attrs["data-product-post-editor"] = "true"

    @cached_property
    def media(self):
        return super().media + Media(
            js=["content/composer.js"], css={"all": ["content/composer.css"]}
        )
