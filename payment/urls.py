from django.urls import path

from payment.views import payment_canceled, payment_completed, payment_process

app_name = "payment"

urlpatterns = [
    path("process/", payment_process, name="payment_process"),
    path("completed/", payment_completed, name="payment_completed"),
    path("canceled/", payment_canceled, name="payment_canceled"),
]
