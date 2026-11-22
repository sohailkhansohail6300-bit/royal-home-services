from .models import Category


def categories_processor(request):
    return {
        "nav_categories": Category.objects.all()
    }


def seo_processor(request):
    """Supplies ``seo`` (head metadata) for the fixed pages. The category page builds its
    own ``seo`` in its view, which takes precedence over this processor."""
    from .seo import STATIC_URL_NAMES, static_page_seo

    match = getattr(request, "resolver_match", None)
    name = match.url_name if match else None
    if name in STATIC_URL_NAMES:
        return {"seo": static_page_seo(request, name)}
    return {}
