from django.urls import path, include
from wagtail.admin import urls as admin_urls
from wagtail.admin.auth import require_admin_access
from content import views
urlpatterns = [
    path('admin/images/<int:image_id>/',require_admin_access(views.ImageEditView.as_view())),
    path('admin/',include(admin_urls)),
    path('',views.home,name='home'),
    path('branches/',views.branches,name='branches'),
    path('api/v1/site/',views.site_api,name='site-api'),
    path('api/v1/branches/',views.branches_api,name='branches-api'),
    path('images/display/<int:pk>/',views.display_image,name='display-image'),
    path('cms-files/<path:name>',views.private_file,name='private-file'),
]
handler404 = 'content.views.not_found'
handler500 = 'content.views.server_error'
# No Wagtail page serving, public document API, MEDIA_URL or signed image route.
