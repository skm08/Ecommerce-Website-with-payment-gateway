from django.db import models


class Coupon(models.Model):
    code=models.CharField(max_length=200, unique=True)
    discount=models.PositiveIntegerField(help_text='discount percent')
    active=models.BooleanField(default=True)
    active_date=models.DateField()
    expiry_date=models.DateField()
    required_amount_to_use_coupon = models.PositiveBigIntegerField()
    created_date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.code