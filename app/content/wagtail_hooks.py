from wagtail.snippets.models import register_snippet
from .admin import SiteViewSet, BranchViewSet, TrainerViewSet
register_snippet(SiteViewSet)
register_snippet(BranchViewSet)
register_snippet(TrainerViewSet)
from wagtail import hooks
from .post_admin import PostViewSet
from .models import Post
register_snippet(PostViewSet)

@hooks.register('construct_snippet_action_menu')
def post_restore_is_draft_only(menu_items, request, context):
    if context.get('model') is Post and context.get('view') == 'revisions_revert':
        menu_items[:] = [item for item in menu_items if item.name != 'action-publish']
