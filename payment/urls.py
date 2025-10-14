from django.urls import path

from payment import views

app_name = "payment"

urlpatterns = [
    path("process/", views.PaymentProcessView.as_view(), name="payment_process"),
    path("completed/", views.PaymentCompletedView.as_view(), name="payment_completed"),
    path("canceled/", views.PaymentCanceledView.as_view(), name="payment_canceled"),
]
