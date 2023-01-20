from django.core.paginator import Paginator
from django.db.models import QuerySet


def get_page_pagi_func(request, objects, posts_on_page) -> QuerySet:
    """
    функция пагинации для views, вынесена в отдельный модуль
    """
    paginator = Paginator(objects, posts_on_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
