from django.http import HttpResponseForbidden
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin


class SpikeBoundaryMiddleware(MiddlewareMixin):
    """Small experiment boundary, coupled to pinned Wagtail URL names."""
    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if not request.user.is_superuser:
            image_delete = match.namespace == "wagtailimages" and match.url_name in {
                "delete", "delete_multiple", "delete_upload_multiple"
            }
            bulk_delete = (
                match.url_name == "wagtail_bulk_action" and view_kwargs.get("action") == "delete"
                and (view_kwargs.get("app_label"), view_kwargs.get("model_name")) in {("wagtailimages", "image"), ("posts", "post")}
            )
            if image_delete or bulk_delete:
                return HttpResponseForbidden("Permanent deletion is disabled in SPIKE-01.")

    def process_response(self, request, response):
        # Includes denied responses, preview, Wagtail's own image preview and JSON.
        if not request.path.startswith("/static/"):
            add_never_cache_headers(response)
        return response
