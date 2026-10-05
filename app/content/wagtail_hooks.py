from wagtail.snippets.models import register_snippet
from .admin import SiteViewSet, BranchViewSet, TrainerViewSet
register_snippet(SiteViewSet)
register_snippet(BranchViewSet)
register_snippet(TrainerViewSet)
