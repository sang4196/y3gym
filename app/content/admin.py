from django.core.exceptions import ValidationError
from wagtail.snippets.views.snippets import CreateView, EditView, SnippetViewSet
from wagtail.permission_policies.base import ModelPermissionPolicy
from .models import Branch, SiteContent, Trainer
from .forms import BranchForm, ContentForm

class NoDeletePolicy(ModelPermissionPolicy):
    def user_has_permission(self, user, action):
        if action == 'delete': return False
        if self.model is SiteContent and action == 'add' and SiteContent.objects.exists(): return False
        return super().user_has_permission(user, action)
    def user_has_any_permission(self, user, actions):
        return any(self.user_has_permission(user, action) for action in actions)

class SaveErrorMixin:
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as error:
            self.produced_error_code = 'validation_error'
            self.produced_error_message = ' '.join(error.messages)
            form.add_error(None, self.produced_error_message)
            return self.form_invalid(form)

class ContentCreateView(SaveErrorMixin, CreateView): pass
class ContentEditView(SaveErrorMixin, EditView): pass

class ContentViewSet(SnippetViewSet):
    add_to_admin_menu = True
    create_view_class = ContentCreateView
    edit_view_class = ContentEditView
    @property
    def permission_policy(self):
        return NoDeletePolicy(self.model)

SiteContent.base_form_class = ContentForm
Branch.base_form_class = BranchForm
Trainer.base_form_class = ContentForm
class SiteViewSet(ContentViewSet):
    model = SiteContent
    menu_label = '홈페이지 기본 정보'
    icon = 'home'
class BranchViewSet(ContentViewSet):
    model = Branch
    menu_label = '지점'
    icon = 'site'
    list_display = ['name','is_public','is_main','sort_order']

class TrainerViewSet(ContentViewSet):
    model = Trainer
    menu_label = '트레이너'
    icon = 'user'
    list_display = ['name', 'branch', 'job_title', 'is_public', 'sort_order']
    list_filter = ['branch', 'is_public']
    search_fields = ['name', 'job_title']

from .models import Popup
Popup.base_form_class = ContentForm

class PopupViewSet(ContentViewSet):
    model = Popup
    menu_label = '기간제 팝업'
    icon = 'doc-full'
    list_display = ['title', 'post', 'enabled', 'display_status', 'starts_at', 'ends_at', 'priority']
    list_filter = ['enabled']
    search_fields = ['title', 'message']
    copy_view_enabled = False
