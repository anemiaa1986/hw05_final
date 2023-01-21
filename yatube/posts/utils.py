from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.core.handlers.wsgi import WSGIRequest


def get_page_pagi_func(
    request: WSGIRequest,
    objects: QuerySet,
    posts_on_page: int
) -> Page:
    """
    функция пагинации для views, вынесена в отдельный модуль
    """
    paginator = Paginator(objects, posts_on_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
