from decimal import Decimal

from django.conf import settings

from .models import Coupon


class Cart(object):
    """Session-backed shopping cart.

    All monetary values are stored and computed as ``Decimal`` to avoid
    floating-point rounding errors.
    """

    def __init__(self, request):
        self.session = request.session
        self.cart_id = settings.CART_ID
        self.coupon_id = settings.COUPON_ID

        cart = self.session.get(self.cart_id)
        coupon = self.session.get(self.coupon_id)
        self.cart = self.session[self.cart_id] = cart if cart else {}
        self.coupon = self.session[self.coupon_id] = coupon if coupon else None

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def update(self, product_id, quantity=1):
        product = Product.objects.get(id=product_id)
        self.session[self.cart_id].setdefault(
            str(product_id), {"quantity": 0, "subtotal": "0"}
        )
        updated_quantity = (
            self.session[self.cart_id][str(product_id)]["quantity"] + quantity
        )
        self.session[self.cart_id][str(product_id)]["quantity"] = updated_quantity
        self.session[self.cart_id][str(product_id)]["subtotal"] = str(
            Decimal(updated_quantity) * Decimal(product.price)
        )

        if updated_quantity < 1:
            del self.session[self.cart_id][str(product_id)]
        self.save()

    def add_coupon(self, coupon_id):
        self.session[self.coupon_id] = coupon_id
        self.coupon = coupon_id
        self.save()

    def remove_coupon(self):
        if self.coupon_id in self.session:
            del self.session[self.coupon_id]
            self.coupon = None
            self.save()

    # ------------------------------------------------------------------
    # Iteration / length
    # ------------------------------------------------------------------
    def __iter__(self):
        products = Product.objects.filter(id__in=list(self.cart.keys()))
        cart = self.cart.copy()

        for item in products:
            cart[str(item.id)]["product"] = {
                "id": item.id,
                "title": item.title,
                "category": item.category.title,
                "price": float(item.price),
                "thumbnail": item.thumbnail.url if item.thumbnail else "",
                "slug": item.slug,
            }
            yield cart[str(item.id)]

    def __len__(self):
        return len(list(self.cart.keys()))

    def clear(self):
        try:
            del self.session[self.cart_id]
            del self.session[self.coupon_id]
        except KeyError:
            pass
        self.coupon = None
        self.cart = {}
        self.save()

    def restore_after_logout(self, cart=None, coupon=None):
        self.cart = self.session[self.cart_id] = cart or {}
        self.coupon = self.session[self.coupon_id] = coupon
        self.save()

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------
    def total(self):
        amount = sum(
            (Decimal(product["subtotal"]) for product in self.cart.values()),
            Decimal("0"),
        )

        if self.coupon:
            coupon = Coupon.objects.get(id=self.coupon)
            amount -= amount * (Decimal(coupon.discount) / Decimal(100))
        return amount.quantize(Decimal("0.01"))

    def subtotal(self):
        return sum(
            (Decimal(product["subtotal"]) for product in self.cart.values()),
            Decimal("0"),
        ).quantize(Decimal("0.01"))

    def save(self):
        self.session.modified = True


# Imported at the bottom to avoid a circular import at module load time.
from product.models import Product  # noqa: E402