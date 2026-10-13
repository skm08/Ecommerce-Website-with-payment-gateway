"""Thin wrappers around the PayPal Checkout SDK.

All PayPal interactions happen server-side so secrets never touch the
browser. The SDK is configured from settings; in dev without credentials
the functions raise a clear ``RuntimeError`` instead of silently failing.
"""

from decimal import Decimal

from django.conf import settings

from paypalcheckoutsdk.core import (
    PayPalHttpClient,
    SandboxEnvironment,
    LiveEnvironment,
)
from paypalcheckoutsdk.orders import (
    OrdersCaptureRequest,
    OrdersCreateRequest,
)


def _environment():
    if (settings.PAYPAL_MODE or "").lower() == "live":
        return LiveEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID,
            client_secret=settings.PAYPAL_SECRET_ID,
        )
    return SandboxEnvironment(
        client_id=settings.PAYPAL_CLIENT_ID,
        client_secret=settings.PAYPAL_SECRET_ID,
    )


def _client():
    """Build an authenticated PayPal HTTP client.

    The client transparently fetches and caches OAuth access tokens, so
    callers never need to manage auth headers themselves.
    """
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_SECRET_ID:
        raise RuntimeError(
            "PayPal credentials are not configured. Set PAYPAL_CLIENT_ID and "
            "PAYPAL_SECRET_ID in your .env file."
        )
    return PayPalHttpClient(_environment())


def _to_dict(obj):
    """Normalise a PayPal SDK response result into a plain dict."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except TypeError:
            return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return obj


def create_paypal_order(amount, reference_id):
    """Create a PayPal order for ``amount`` (Decimal) tied to ``reference_id``.

    Returns the PayPal order response as a dict (with at least an ``id``).
    """
    client = _client()

    request = OrdersCreateRequest()
    request.prefer("return=representation")
    request.request_body(
        {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(reference_id),
                    "amount": {
                        "value": str(Decimal(amount).quantize(Decimal("0.01"))),
                        "currency_code": "USD",
                    },
                }
            ],
            "application_context": {
                "return_url": f"{settings.FRONTEND_URL}/checkout/capture/",
                "cancel_url": f"{settings.FRONTEND_URL}/checkout/",
                "brand_name": "Ecommerce Showcase",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
            },
        }
    )

    response = client.execute(request)
    return _to_dict(response.result)


def capture_paypal_order(paypal_order_id):
    """Capture a previously created PayPal order.

    Returns the capture response as a dict.
    """
    client = _client()

    request = OrdersCaptureRequest(paypal_order_id)
    request.request_body({})

    response = client.execute(request)
    return _to_dict(response.result)