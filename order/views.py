from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from cart.carts import Cart
from product.models import Product

from .forms import CheckoutForm
from .models import Order, OrderItem
from .services import capture_paypal_order, create_paypal_order


class Checkout(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy("login")

    def get(self, *args, **kwargs):
        cart = Cart(self.request)
        if len(cart) == 0:
            messages.warning(self.request, "Your cart is empty.")
            return redirect("cart")
        form = CheckoutForm()
        context = {
            "form": form,
            "cart_total": cart.total(),
            "paypal_client_id": settings.PAYPAL_CLIENT_ID,
            "paypal_mode": settings.PAYPAL_MODE,
        }
        return render(self.request, "order/checkout.html", context)

    def post(self, *args, **kwargs):
        cart = Cart(self.request)
        if len(cart) == 0:
            return JsonResponse(
                {"success": False, "errors": {"__all__": ["Your cart is empty."]}}
            )

        form = CheckoutForm(self.request.POST)
        if not form.is_valid():
            return JsonResponse(
                {"success": False, "errors": dict(form.errors.items())}
            )

        data = form.cleaned_data
        order = Order.objects.create(
            user=self.request.user,
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            city=data["city"],
            zip_code=data["zip_code"],
            address=data["address"],
            subtotal=cart.subtotal(),
            total=cart.total(),
            payment_method="paypal",
            paid=False,
        )

        for item in cart:
            product = get_object_or_404(Product, id=item["product"]["id"])
            order_item = OrderItem.objects.create(
                product=product,
                price=Decimal(product.price),
                quantity=item["quantity"],
            )
            order.order_items.add(order_item)

        # Ask PayPal for an order id the frontend can render.
        try:
            paypal_order = create_paypal_order(cart.total(), order.id)
            order.paypal_order_id = paypal_order.get("id")
            order.save()
        except Exception as exc:  # pragma: no cover - network path
            order.delete()
            return JsonResponse(
                {"success": False, "errors": {"__all__": [str(exc)]}}
            )

        return JsonResponse(
            {
                "success": True,
                "order_id": order.id,
                "paypal_order_id": order.paypal_order_id,
                "amount": str(cart.total()),
            }
        )


class CaptureOrder(LoginRequiredMixin, generic.View):
    """Server-side PayPal order capture -> marks the Order paid."""

    login_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        order_id = request.POST.get("order_id") or request.GET.get("order_id")
        if not order_id:
            return JsonResponse(
                {"success": False, "error": "missing order_id"}, status=400
            )

        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.paid:
            return JsonResponse({"success": True, "already_paid": True})

        try:
            capture = capture_paypal_order(order.paypal_order_id)
        except Exception as exc:  # pragma: no cover - network path
            return JsonResponse(
                {"success": False, "error": str(exc)}, status=400
            )

        status = (capture.get("status") or "").upper()
        if status != "COMPLETED":
            order.status = "Cancelled"
            order.save()
            return JsonResponse(
                {"success": False, "error": f"PayPal status: {status}"}, status=400
            )

        purchase = capture.get("purchase_units", [{}])[0]
        payments = purchase.get("payments", {}).get("captures", [{}])
        capture_id = payments[0].get("id") if payments else None

        order.paid = True
        order.transaction_id = capture_id or order.id
        order.status = "Received"
        order.save()

        cart = Cart(request)
        cart.clear()

        messages.success(request, "Payment successful! Thank you for your order.")
        return JsonResponse(
            {
                "success": True,
                "order_id": order.id,
                "capture_id": capture_id,
            }
        )


class OrderHistory(LoginRequiredMixin, generic.TemplateView):
    template_name = "order/order-history.html"
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = Order.objects.filter(user=self.request.user)
        return context
