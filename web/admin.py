from django.contrib import admin

from web.models import Category, Client, Order, OrderDetail, Product

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    readonly_fields = ["created"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "image", "description", "price"]
    readonly_fields = ["created", "updated"]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["user", "dni", "sex", "phone", "birth", "address"]
    readonly_fields = ["created", "updated"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["client", "registration_date", "order_num", "total_price",
                    "status"]


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ["order", "product", "quantity", "subtotal"]
