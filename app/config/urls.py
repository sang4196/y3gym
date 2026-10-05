from django.urls import path, include
from wagtail.admin import urls as admin_urls
from wagtail.admin.auth import require_admin_access
from content import views
from content import post_views, popup_views
urlpatterns = [
    path('api/v1/popups/active/',popup_views.active,name='active-popups'),
    path('posts/',post_views.posts,name='posts'),
    path('posts/<int:pk>/',post_views.post_detail,name='post-detail'),
    path('api/v1/posts/',post_views.posts_api,name='posts-api'),
    path('api/v1/posts/<int:pk>/',post_views.post_api,name='post-api'),
    path('admin/images/<int:image_id>/',require_admin_access(views.ImageEditView.as_view())),
    path('admin/',include(admin_urls)),
    path('',views.home,name='home'),
    path('branches/',views.branches,name='branches'),
    path('trainers/',views.trainers,name='trainers'),
    path('api/v1/site/',views.site_api,name='site-api'),
    path('api/v1/branches/',views.branches_api,name='branches-api'),
    path('api/v1/trainer-sections/',views.trainer_sections_api,name='trainer-sections-api'),
    path('images/display/<int:pk>/',views.display_image,name='display-image'),
    path('cms-files/<path:name>',views.private_file,name='private-file'),
]
handler404 = 'content.views.not_found'
handler500 = 'content.views.server_error'
# No Wagtail page serving, public document API, MEDIA_URL or signed image route.
