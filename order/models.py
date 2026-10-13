from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from cart.models import Coupon
from product.models import Product


PAYMENT_METHODS = (
    ("paypal", "PayPal"),
    ("cod", "Cash on Delivery"),
)


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product, related_name="ordered", on_delete=models.CASCADE
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"

    @property
    def subtotal(self):
        return (self.price * self.quantity).quantize(Decimal("0.01"))


class Order(models.Model):
    STATUS_CHOICES = (
        ("Received", "Received"),
        ("On the way", "On the way"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE
    )
    order_items = models.ManyToManyField(OrderItem, related_name="orders")
    coupon = models.ForeignKey(
        Coupon, null=True, blank=True, on_delete=models.SET_NULL
    )
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField(max_length=256)
    city = models.CharField(max_length=256)
    zip_code = models.CharField(max_length=128)
    address = models.TextField()
    subtotal = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    shipping_cost = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    total = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS, default="paypal"
    )
    paypal_order_id = models.CharField(
        max_length=64, null=True, blank=True, unique=True,
        help_text="PayPal order id returned by createOrder",
    )
    transaction_id = models.CharField(
        max_length=64, null=True, blank=True,
        help_text="PayPal capture id / transaction id",
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default="Received"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"