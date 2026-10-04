from wagtail.snippets.models import register_snippet
from .admin import SiteViewSet, BranchViewSet
register_snippet(SiteViewSet)
register_snippet(BranchViewSet)
