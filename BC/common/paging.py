from django.core.paginator import Paginator

def pager(request, queryset, per_page=10, block_size=10):

    # page = 문자열 → int 변환 필수
    try:
        page = int(request.GET.get("page", 1))
    except:
        page = 1

    paginator = Paginator(queryset, per_page)

    # 안전하게 페이지 가져오기
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)

    # 진짜 현재 페이지 번호
    current_page = page_obj.number

    current_block = (current_page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1

    if block_end > paginator.num_pages:
        block_end = paginator.num_pages

    block_range = range(block_start, block_end + 1)

    return {
        "page_obj": page_obj,
        "per_page": per_page,
        "block_range": block_range,
        "block_start": block_start,
        "block_end": block_end,
        "paginator": paginator,
        "page_range": paginator.page_range,
        "total_count": paginator.count,
        "current_page": current_page,
        "total_pages": paginator.num_pages,
    }
