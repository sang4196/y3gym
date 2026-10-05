from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseForbidden
from wagtail.snippets.views.snippets import CreateView, EditView, UnpublishView
from .admin import ContentViewSet
from .forms import ContentForm
from .locking import content_transaction
from .models import Post
from .post_body import validate_images
from .post_models import STALE_POST


class PostForm(ContentForm):
    def is_valid(self):
        valid = super().is_valid()
        if valid:
            try:
                validate_images(self.instance, self.for_user)
            except (ValidationError, PermissionDenied) as error:
                self.add_error(None, str(error))
                valid = False
        return valid


class PostSaveMixin:
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        # Every explicit save creates an immutable revision and a fresh version token.
        self.autosave_enabled = False

    def form_valid(self, form):
        if self.request.POST.get('overwrite_revision_id') or self.request.POST.get('overwrite_revision') or (
            self.view_name == 'revisions_revert' and 'action-publish' in self.request.POST
        ):
            return HttpResponseForbidden('이전 버전은 초안으로 복원한 뒤 다시 열어 공개하세요.')
        try:
            # Encompasses form/Revision saves AND Wagtail's later publish action.
            with content_transaction():
                return super().form_valid(form)
        except ValidationError as error:
            self.produced_error_code = 'validation_error'
            self.produced_error_message = ' '.join(error.messages)
            form.add_error(None, self.produced_error_message)
            return self.form_invalid(form)


class PostCreateView(PostSaveMixin, CreateView):
    pass


class PostEditView(PostSaveMixin, EditView):
    pass


class PostUnpublishView(UnpublishView):
    template_name = 'content/admin/post_unpublish.html'

    def unpublish(self):
        with content_transaction():
            if self.request.POST.get('edit_version') != str(self.object.edit_version):
                raise ValidationError(STALE_POST)
            self.object.unpublish(user=self.request.user)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ValidationError as error:
            return self.render_to_response(self.get_context_data(error=' '.join(error.messages)), status=409)


Post.base_form_class = PostForm


class PostViewSet(ContentViewSet):
    model = Post
    menu_label = '공지·이벤트'
    icon = 'doc-full'
    create_view_class = PostCreateView
    edit_view_class = PostEditView
    unpublish_view_class = PostUnpublishView
    index_template_name = 'content/admin/post_index.html'
    copy_view_enabled = False
    list_display = ['title', 'category', 'status_string', 'first_published_at']
    search_fields = ['title']
