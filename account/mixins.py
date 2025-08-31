from typing import TYPE_CHECKING

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy


class AnonymousRequiredMixin(UserPassesTestMixin):
    login_redirect_url = reverse_lazy("account:user_account")

    if TYPE_CHECKING:
        request: HttpRequest

    def test_func(self) -> bool:
        return not self.request.user.is_authenticated

    def handle_no_permission(self) -> HttpResponseRedirect:
        return redirect(self.login_redirect_url)
