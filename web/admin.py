from django.contrib import admin

from web.models import Category, Product, Brand

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    readonly_fields = ["created"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "image", "description", "price"]
    readonly_fields = ["created", "updated"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "fundator", "image"]
    readonly_fields = ["created"]
