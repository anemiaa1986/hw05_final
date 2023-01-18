from django.core.paginator import Paginator


COUNT_OF_POSTS = 10


def get_page_pagi_func(queryset, request):
    paginator = Paginator(queryset, COUNT_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_obj': page_obj,
    }