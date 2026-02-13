PER_PAGE = 5


def paginate(total: int, page: int, per_page: int = PER_PAGE) -> tuple[int, int, int]:
    """Return (offset, limit, total_pages) for the given page."""
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page
    return offset, per_page, total_pages
