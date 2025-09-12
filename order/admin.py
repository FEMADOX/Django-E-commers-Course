from django.contrib import admin

from order.models import Order, OrderDetail


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["client", "registration_date", "order_num", "total_price", "status"]


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ["order", "product", "quantity", "subtotal"]
