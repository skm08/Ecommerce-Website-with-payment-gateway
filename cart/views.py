from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import generic

from cart.carts import Cart
from product.models import Product

from .models import Coupon


class AddToCart(generic.View):
    def post(self, *args, **kwargs):
        product = get_object_or_404(Product, id=kwargs.get("product_id"))
        cart = Cart(self.request)
        cart.update(product.id, 1)
        return redirect("cart")


class CartItems(generic.TemplateView):
    template_name = "cart/cart.html"

    def get(self, request, *args, **kwargs):
        product_id = request.GET.get("product_id", None)
        quantity = request.GET.get("quantity", None)
        clear = request.GET.get("clear", False)
        cart = Cart(request)

        if product_id and quantity:
            product = get_object_or_404(Product, id=product_id)
            if int(quantity) > 0:
                if product.in_stock:
                    cart.update(int(product_id), int(quantity))
                    return redirect("cart")
                messages.warning(request, "Out of stock!")
                return redirect("cart")
            else:
                cart.update(int(product_id), int(quantity))
                return redirect("cart")

        if clear:
            cart.clear()
            return redirect("cart")

        return super().get(request, *args, **kwargs)


class AddCoupon(generic.View):
    def post(self, *args, **kwargs):
        from django.utils import timezone

        code = self.request.POST.get("coupon", "")
        coupon = Coupon.objects.filter(code__iexact=code, active=True)
        cart = Cart(self.request)

        if coupon.exists():
            coupon = coupon.first()
            current_date = timezone.now().date()

            if coupon.is_expired:
                messages.warning(self.request, "The coupon has expired!")
                return redirect("cart")

            if coupon.is_not_yet_active:
                messages.warning(
                    self.request, "The coupon is not yet available!"
                )
                return redirect("cart")

            if coupon.has_reached_limit:
                messages.warning(
                    self.request, "This coupon has been fully used."
                )
                return redirect("cart")

            if cart.subtotal() < coupon.required_amount_to_use_coupon:
                messages.warning(
                    self.request,
                    f"You have to shop at least "
                    f"{coupon.required_amount_to_use_coupon} to use coupon.",
                )
                return redirect("cart")

            cart.add_coupon(coupon.id)
            messages.success(self.request, "Your coupon has been applied!")
            return redirect("cart")

        messages.warning(self.request, "Invalid coupon code!")
        return redirect("cart")