from django.contrib import admin

from account.models import Client

# Register your models here.


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["user", "dni", "sex", "phone", "birth", "address"]
    readonly_fields = ["created", "updated"]
