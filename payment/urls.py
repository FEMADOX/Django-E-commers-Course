from django.urls import path

from payment.views import payment_process

app_name = "payment"

urlpatterns = [
    path("process/", payment_process, name="payment_process"),
]
