from django.db import models
from django.shortcuts import render
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import DraftStateMixin, PreviewableMixin, RevisionMixin
from wagtail.snippets.models import register_snippet
from .forms import PostForm
from .widgets import PostRichTextArea


@register_snippet
class Post(DraftStateMixin, RevisionMixin, PreviewableMixin, models.Model):
    base_form_class = PostForm
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=[("notice", "Notice"), ("event", "Event")])
    body = RichTextField(features=["h2", "bold", "italic", "ol", "ul", "link", "image"])
    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    panels = [
        FieldPanel("title", heading="제목"),
        FieldPanel("category", heading="분류"),
        FieldPanel(
            "body",
            widget=PostRichTextArea,
            classname="spike-post-body",
            heading="본문",
        ),
        FieldPanel(
            "cover_image",
            heading="대표 이미지",
            help_text="글 상단에 표시되는 이미지입니다. 본문 이미지는 본문에서 넣습니다.",
        ),
    ]

    def __str__(self):
        return self.title

    def get_preview_template(self, request, mode_name):
        return "posts/detail.html"

    def serve_preview(self, request, mode_name):
        from .publication import serialize_post
        return render(request, "posts/detail.html", {"post": serialize_post(self, request, preview=True), "preview": True})

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("post-html", args=[self.pk])
