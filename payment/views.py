import stripe
from django.http import HttpRequest

from edshop.settings import STRIPE_API

# from django.shortcuts import redirect, render


# # Create your views here.

stripe.api_key = STRIPE_API


def payment_process(request: HttpRequest):
    # order_id = request.session.get("order_id", None)
    pass
