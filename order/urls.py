from django.urls import path

from .views import CaptureOrder, Checkout, OrderHistory

urlpatterns = [
    path("checkout/", Checkout.as_view(), name="checkout"),
    path(
        "checkout/capture/",
        CaptureOrder.as_view(),
        name="checkout-capture",
    ),
    path("orders/", OrderHistory.as_view(), name="order-history"),
]