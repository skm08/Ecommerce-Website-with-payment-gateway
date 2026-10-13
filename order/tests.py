"""Tests for the order/checkout flow."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from cart.models import Coupon
from order.models import Order, OrderItem
from product.models import Category, Product

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="alice", email="a@example.com", password="secret"
    )


@pytest.fixture
def category(db):
    return Category.objects.create(title="Electronics", slug="electronics")


@pytest.fixture
def product(category):
    return Product.objects.create(
        category=category,
        title="Widget",
        slug="widget",
        price="20.00",
        thumbnail="https://example.com/widget.jpg",
    )


def add_to_cart(client, product, quantity=2):
    """Add items to the session-backed cart via the view."""
    # Clear any existing cart state first so the count is deterministic.
    client.get("/cart/?clear=true")
    # The cart view *adds* to the existing quantity, so a single call with
    # the target quantity is enough.
    client.get("/cart/", {"product_id": product.id, "quantity": quantity})


@pytest.mark.django_db
def test_checkout_requires_login(client, product):
    add_to_cart(client, product)
    response = client.get("/checkout/")
    assert response.status_code == 302  # redirect to login


@pytest.mark.django_db
def test_checkout_creates_order_and_paypal_id(client, user, product):
    client.force_login(user)
    add_to_cart(client, product, quantity=2)

    fake_order = {"id": "PAYPAL-ORDER-123"}
    with patch("order.views.create_paypal_order", return_value=fake_order):
        response = client.post(
            "/checkout/",
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "a@example.com",
                "city": "Townsville",
                "zip_code": "12345",
                "address": "1 Main St",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["paypal_order_id"] == "PAYPAL-ORDER-123"

    order = Order.objects.get()
    assert order.user == user
    assert order.first_name == "Alice"
    assert order.subtotal == Decimal("40.00")
    assert order.total == Decimal("40.00")
    assert order.paid is False
    assert order.paypal_order_id == "PAYPAL-ORDER-123"
    assert order.order_items.count() == 1
    assert order.order_items.first().quantity == 2


@pytest.mark.django_db
def test_capture_marks_order_paid(client, user, product):
    client.force_login(user)
    add_to_cart(client, product, quantity=1)

    order = Order.objects.create(
        user=user,
        first_name="Alice",
        last_name="Smith",
        email="a@example.com",
        city="Townsville",
        zip_code="12345",
        address="1 Main St",
        subtotal=Decimal("20.00"),
        total=Decimal("20.00"),
        paypal_order_id="PAYPAL-ORDER-XYZ",
        paid=False,
    )

    fake_capture = {
        "status": "COMPLETED",
        "purchase_units": [
            {"payments": {"captures": [{"id": "CAP-987"}]}}
        ],
    }
    with patch("order.views.capture_paypal_order", return_value=fake_capture):
        response = client.post(
            "/checkout/capture/", data={"order_id": order.id}
        )

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.paid is True
    assert order.transaction_id == "CAP-987"
    assert order.status == "Received"


@pytest.mark.django_db
def test_coupon_expired_rejected(client, user, product):
    client.force_login(user)
    add_to_cart(client, product, quantity=1)

    expired = Coupon.objects.create(
        code="EXPIRED",
        discount=10,
        active_date=date(2020, 1, 1),
        expiry_date=date(2021, 1, 1),
        required_amount_to_use_coupon=50,
    )
    response = client.post("/add-coupon/", data={"coupon": "EXPIRED"})
    assert response.status_code == 302
    # Coupon must NOT be applied to the session.
    assert client.session.get("coupon") != expired.id


@pytest.mark.django_db
def test_order_history_requires_login(client):
    response = client.get("/orders/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_order_history_lists_orders(client, user, product):
    client.force_login(user)
    Order.objects.create(
        user=user,
        first_name="Alice",
        last_name="Smith",
        email="a@example.com",
        city="Townsville",
        zip_code="12345",
        address="1 Main St",
        subtotal=Decimal("20.00"),
        total=Decimal("20.00"),
        paid=True,
        status="Delivered",
    )
    response = client.get("/orders/")
    assert response.status_code == 200
    assert b"Alice" in response.content or b"Smith" in response.content