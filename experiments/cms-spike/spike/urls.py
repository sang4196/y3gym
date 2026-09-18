from django.urls import include, path
from wagtail.admin import urls as admin_urls
from wagtail.admin.auth import require_admin_access
from posts import views

urlpatterns = [
    path("admin/images/<int:image_id>/", require_admin_access(views.SpikeImageEditView.as_view())),
    path("admin/", include(admin_urls)),
    path("cms-files/<path:name>", views.private_file, name="private-file"),
    path("spike/display/<int:image_id>/", views.display_image, name="display-image"),
    path("spike/posts/<int:pk>/", views.post_html, name="post-html"),
    path("spike/posts/<int:pk>/json/", views.post_json, name="post-json"),
]
# No MEDIA_URL, document serve, dynamic signed image serve or Page serve routes.
