from flask import request


def paginate_query(query, max_per_page=30, default_per_page=10, args=None):
    """
    Apply pagination to a SQLAlchemy query.

    Pagination values are resolved in this order:
        1. `args` dict (validated query args from a Marshmallow schema), if provided
        2. Flask `request.args` (raw query string) as a fallback

    Query params:
        ?page=1         (default: 1)
        ?per_page=10    (default: 10, max: 30)

    Args:
        query: SQLAlchemy query to paginate.
        max_per_page: hard cap on per_page.
        default_per_page: fallback page size.
        args: optional dict of already-validated args (e.g. from
              `@blueprint.arguments(..., location="query")`).

    Returns:
        dict with keys: items, page, per_page, total, pages, count
        - items: list of model instances for the current page
        - page: current page number
        - per_page: items per page
        - total: total number of items across all pages
        - pages: total number of pages
        - count: number of items returned on this page
    """
    if args:
        page = args.get('page', 1) or 1
        per_page = args.get('per_page', default_per_page) or default_per_page
    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', default_per_page, type=int)

    # Enforce bounds
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = default_per_page
    if per_page > max_per_page:
        per_page = max_per_page

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": pagination.items,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "count": len(pagination.items),
    }
