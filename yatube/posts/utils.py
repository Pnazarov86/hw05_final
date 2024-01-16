from django.core.paginator import Paginator

from .constants import NUMBER_OF_POSTS


def get_page_context(posts, request):
    """Пагинация."""
    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
