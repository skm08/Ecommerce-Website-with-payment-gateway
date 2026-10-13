"""Tests for the session-backed shopping cart."""
from decimal import Decimal

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from cart.carts import Cart
from cart.models import Coupon
from product.models import Category, Product


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


@pytest.fixture
def session_cart(db):
    factory = RequestFactory()
    request = factory.get("/")
    request.session = SessionStore()
    return Cart(request), request


def test_add_and_update(session_cart, product):
    cart, _ = session_cart
    cart.update(product.id, 2)
    assert len(cart) == 1
    assert cart.cart[str(product.id)]["quantity"] == 2
    assert Decimal(cart.cart[str(product.id)]["subtotal"]) == Decimal("40.00")


def test_remove_when_quantity_zero(session_cart, product):
    cart, _ = session_cart
    cart.update(product.id, 1)
    assert len(cart) == 1
    cart.update(product.id, -1)
    assert len(cart) == 0


def test_total_with_coupon(session_cart, product, db):
    cart, _ = session_cart
    cart.update(product.id, 10)  # 10 x 20.00 = 200.00
    coupon = Coupon.objects.create(
        code="SAVE10",
        discount=10,
        active_date="2020-01-01",
        expiry_date="2030-01-01",
        required_amount_to_use_coupon=50,
    )
    cart.add_coupon(coupon.id)
    # 200.00 - 10% = 180.00
    assert cart.total() == Decimal("180.00")


def test_iter_yields_product_snapshot(session_cart, product):
    cart, _ = session_cart
    cart.update(product.id, 1)
    items = list(cart)
    assert len(items) == 1
    assert items[0]["product"]["title"] == "Widget"
    assert items[0]["product"]["slug"] == "widget"


def test_clear_removes_items(session_cart, product):
    cart, _ = session_cart
    cart.update(product.id, 3)
    assert len(cart) == 1
    cart.clear()
    assert len(cart) == 0
    assert cart.coupon is None