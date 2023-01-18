from django.core.paginator import Paginator


def get_page_pagi_func(request, object, magic_numbers):
    paginator = Paginator(object, magic_numbers)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
