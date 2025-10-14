from django.urls import path

from web.views import (
    FilterByBrandView,
    FilterByCategoryView,
    IndexView,
    ProductDetailView,
    SearchProductTitleView,
)

app_name = "web"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path(
        "by-category/<int:category_id>",
        FilterByCategoryView.as_view(),
        name="filter_by_category",
    ),
    path(
        "by-title/",
        SearchProductTitleView.as_view(),
        name="search_product_title",
    ),
    path(
        "product/<int:product_id>",
        ProductDetailView.as_view(),
        name="product_detail",
    ),
    path(
        "by-brand/<int:brand_id>",
        FilterByBrandView.as_view(),
        name="filter_by_brand",
    ),
]
