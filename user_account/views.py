from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views import generic

from cart.carts import Cart
import copy

from .forms import (
    ChangePasswordForm,
    LoginForm,
    ResetPasswordConfirmForm,
    SendEmailForm,
    UserRegistrationForm,
)
from .mixins import LogoutRequiredMixin


@method_decorator(never_cache, name="dispatch")
class Login(LogoutRequiredMixin, generic.View):
    def get(self, *args, **kwargs):
        form = LoginForm()
        context = {"form": form}
        return render(self.request, "account/login.html", context)

    def post(self, *args, **kwargs):
        form = LoginForm(self.request.POST)
        if form.is_valid():
            user = authenticate(
                self.request,
                username=form.cleaned_data.get("username"),
                password=form.cleaned_data.get("password"),
            )
            if user:
                login(self.request, user)
                return redirect("home")
            messages.warning(self.request, "Wrong credentials")
            return redirect("login")
        return render(self.request, "account/login.html", {"form": form})


class Logout(generic.View):
    def get(self, *args, **kwargs):
        cart = Cart(self.request)
        current_cart = copy.deepcopy(cart.cart)
        coupon = copy.deepcopy(cart.coupon)
        logout(self.request)
        cart.restore_after_logout(current_cart, coupon)
        return redirect("login")


@method_decorator(never_cache, name="dispatch")
class Registration(LogoutRequiredMixin, generic.CreateView):
    template_name = "account/registration.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(self.request, "Registration successful!")
        return super().form_valid(form)


@method_decorator(never_cache, name="dispatch")
class ChangePassword(LoginRequiredMixin, generic.FormView):
    template_name = "account/change_password.html"
    form_class = ChangePasswordForm
    login_url = reverse_lazy("login")
    success_url = reverse_lazy("login")

    def get_form_kwargs(self):
        context = super().get_form_kwargs()
        context["user"] = self.request.user
        return context

    def form_valid(self, form):
        user = self.request.user
        user.set_password(form.cleaned_data.get("new_password1"))
        user.save()
        messages.success(self.request, "Password changed successfully!")
        return super().form_valid(form)


class SendEmailToResetPassword(PasswordResetView):
    template_name = "account/password_reset.html"
    form_class = SendEmailForm
    email_template_name = "account/password_reset_email.html"
    subject_template_name = "account/password_reset_subject.txt"


class ResetPasswordConfirm(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    form_class = ResetPasswordConfirmForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(self.request, "Password reset successfully!")
        return super().form_valid(form)