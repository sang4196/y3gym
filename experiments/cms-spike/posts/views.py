from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe
from wagtail.images import get_image_model
from wagtail.images.models import Rendition
from wagtail.images.permissions import permission_policy
from wagtail.images.views.images import EditView
from .publication import DISPLAY_FILTER, is_public_image, published_post, serialize_post


class SpikeImageEditView(EditView):
    @property
    def can_delete(self):
        return self.request.user.is_superuser and super().can_delete


@require_safe
def post_html(request, pk):
    return render(request, "posts/detail.html", {"post": serialize_post(published_post(pk), request)})


@require_safe
def post_json(request, pk):
    return JsonResponse({"data": serialize_post(published_post(pk), request)})


def file_response(field):
    try:
        return FileResponse(field.open("rb"), content_type="image/png" if field.name.lower().endswith(".png") else "image/jpeg")
    except FileNotFoundError as error:
        raise Http404 from error


@require_safe
def private_file(request, name):
    if not (request.user.is_active and request.user.has_perm("wagtailadmin.access_admin")):
        return HttpResponseForbidden("CMS image permission required.")
    # Exact database lookup, never concatenate a supplied path to MEDIA_ROOT.
    image = get_image_model().objects.filter(file=name).first()
    field = image.file if image else None
    if image is None:
        rendition = Rendition.objects.select_related("image").filter(file=name).first()
        if rendition:
            image, field = rendition.image, rendition.file
    if image is None:
        raise Http404
    if not permission_policy.user_has_any_permission_for_instance(request.user, ["choose", "change"], image):
        return HttpResponseForbidden("CMS image permission required.")
    return file_response(field)


@require_safe
def display_image(request, image_id):
    # Session identity deliberately cannot expand this public endpoint.
    if not is_public_image(image_id):
        raise Http404
    try:
        image = get_image_model().objects.get(pk=image_id)
    except get_image_model().DoesNotExist as error:
        raise Http404 from error
    return file_response(image.get_rendition(DISPLAY_FILTER).file)
