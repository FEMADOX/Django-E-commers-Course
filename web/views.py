from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from web.models import Brand, Category, Product

if TYPE_CHECKING:
    from django.core.paginator import _SupportsPagination
    from django.db.models import QuerySet
    from django.http import HttpRequest, HttpResponse


class LandingView(TemplateView):
    """Display the landing page."""

    template_name = "web/landing.html"


class CatalogView(ListView):
    """Display all products with categories and brands navigation."""

    model = Product
    template_name = "web/index.html"
    context_object_name = "products"

    def get_context_data(self, **kwargs):  # noqa: ANN003, ANN201
        """Add categories and brands to context."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["brands"] = Brand.objects.all()
        return context


class FilterByBaseView(ListView):
    """Display products filtered by some criteria."""

    model = Product
    template_name = "web/index.html"
    context_object_name = "products"

    def get_queryset(self) -> QuerySet[Product]:
        """Get filtered products queryset."""
        return super().get_queryset()

    def get_context_data(
        self,
        *,
        object_list: _SupportsPagination | None = None,
        **kwargs: dict,
    ) -> dict[str, Any]:
        """Add categories and brands to context."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["brands"] = Brand.objects.all()
        return context


class FilterByCategoryView(FilterByBaseView):
    """Filter products by category."""

    def get_queryset(self) -> QuerySet[Product]:
        category_id = self.kwargs["category_id"]
        category = get_object_or_404(Category, id=category_id)
        return Product.objects.filter(category=category)


class FilterByBrandView(FilterByBaseView):
    """Filter products by brand."""

    def get_queryset(self) -> QuerySet[Product]:
        brand_id = self.kwargs["brand_id"]
        brand = get_object_or_404(Brand, id=brand_id)
        return Product.objects.filter(brand=brand)


class SearchProductTitleView(ListView):
    """Search products by title."""

    model = Product
    template_name = "web/index.html"
    context_object_name = "products"

    def get_queryset(self) -> QuerySet[Product]:
        """Filter products by search title."""
        if self.request.method == "POST":
            product_title = self.request.POST.get("title", "")
            return Product.objects.filter(title__contains=product_title)
        return Product.objects.all()

    def get_context_data(self, **kwargs):  # noqa: ANN003, ANN201
        """Add categories to context."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # noqa: ANN002, ANN003
        """Handle POST requests for search."""
        return self.get(request, *args, **kwargs)


class ProductDetailView(DetailView):
    """Display detailed view of a single product."""

    model = Product
    template_name = "web/product.html"
    context_object_name = "product"
    pk_url_kwarg = "product_id"
