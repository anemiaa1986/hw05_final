from django.core.paginator import Paginator
from typing import Any


def get_page_pagi_func(request, queryset, posts_on_page) -> Any:
    """
    функция пагинации для views, вынесена в отдельный модуль
    """
    paginator = Paginator(queryset, posts_on_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
