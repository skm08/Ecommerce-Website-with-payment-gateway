from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Discount percentage (0-100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    active = models.BooleanField(default=True)
    active_date = models.DateField()
    expiry_date = models.DateField()
    required_amount_to_use_coupon = models.PositiveBigIntegerField(
        help_text="Minimum cart subtotal required to use the coupon"
    )
    max_uses = models.PositiveIntegerField(
        default=0, help_text="0 = unlimited uses"
    )
    used_count = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return self.code

    @property
    def is_expired(self):
        from django.utils import timezone

        today = timezone.now().date()
        return today > self.expiry_date

    @property
    def is_not_yet_active(self):
        from django.utils import timezone

        today = timezone.now().date()
        return today < self.active_date

    @property
    def has_reached_limit(self):
        return self.max_uses > 0 and self.used_count >= self.max_uses