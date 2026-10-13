"""Tests for the custom user model and auth views."""
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from cart.models import Coupon
from user_account.forms import (
    ChangePasswordForm,
    LoginForm,
    ResetPasswordConfirmForm,
    SendEmailForm,
    UserRegistrationForm,
)

User = get_user_model()


@pytest.mark.django_db
def test_user_model_email_is_unique(db):
    User.objects.create_user(username="alice", email="a@example.com", password="x")
    with pytest.raises(Exception):
        User.objects.create_user(username="bob", email="a@example.com", password="x")


@pytest.mark.django_db
def test_user_model_username_is_unique(db):
    User.objects.create_user(username="alice", email="a@example.com", password="x")
    with pytest.raises(Exception):
        User.objects.create_user(username="alice", email="b@example.com", password="x")


@pytest.mark.django_db
def test_registration_form_rejects_duplicate_username(db):
    User.objects.create_user(username="alice", email="a@example.com", password="x")
    form = UserRegistrationForm(
        data={
            "username": "alice",
            "email": "b@example.com",
            "password": "secret",
            "password2": "secret",
        }
    )
    assert not form.is_valid()
    assert "username" in form.errors


@pytest.mark.django_db
def test_registration_form_rejects_password_mismatch(db):
    form = UserRegistrationForm(
        data={
            "username": "alice",
            "email": "a@example.com",
            "password": "secret",
            "password2": "different",
        }
    )
    assert not form.is_valid()
    assert "password2" in form.errors


@pytest.mark.django_db
def test_registration_creates_user(db):
    form = UserRegistrationForm(
        data={
            "username": "alice",
            "email": "a@example.com",
            "password": "secret",
            "password2": "secret",
        }
    )
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.id is not None
    assert user.check_password("secret")


@pytest.mark.django_db
def test_login_view_redirects_when_authenticated(client, db):
    user = User.objects.create_user(username="alice", email="a@example.com", password="secret")
    client.force_login(user)
    response = client.get("/login/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_login_view_accepts_email(client, db):
    User.objects.create_user(username="alice", email="a@example.com", password="secret")
    response = client.post(
        "/login/",
        data={"username": "a@example.com", "password": "secret"},
    )
    assert response.status_code == 302  # redirect to home on success


@pytest.mark.django_db
def test_logout_preserves_cart(client, db):
    user = User.objects.create_user(username="alice", email="a@example.com", password="secret")
    client.force_login(user)
    # Add an item to the cart.
    from product.models import Category, Product

    category = Category.objects.create(title="Electronics", slug="electronics")
    product = Product.objects.create(
        category=category,
        title="Widget",
        slug="widget",
        price="20.00",
        thumbnail="https://example.com/widget.jpg",
    )
    client.post("/add-to-cart/%d/" % product.id)
    client.get("/logout/")
    # Cart should survive the logout.
    assert client.session.get("cart", {}).get(str(product.id), {}).get("quantity", 0) == 1


@pytest.mark.django_db
def test_change_password_requires_current(client, db):
    user = User.objects.create_user(username="alice", email="a@example.com", password="old-secret")
    client.force_login(user)
    response = client.post(
        "/change-password/",
        data={
            "current_password": "wrong",
            "new_password1": "new-secret",
            "new_password2": "new-secret",
        },
    )
    assert response.status_code == 200  # form re-rendered with errors
    user.refresh_from_db()
    assert not user.check_password("new-secret")


@pytest.mark.django_db
def test_change_password_success(client, db):
    user = User.objects.create_user(username="alice", email="a@example.com", password="old-secret")
    client.force_login(user)
    response = client.post(
        "/change-password/",
        data={
            "current_password": "old-secret",
            "new_password1": "new-secret",
            "new_password2": "new-secret",
        },
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password("new-secret")


@pytest.mark.django_db
def test_password_reset_email_form_validates_known_email(db):
    User.objects.create_user(username="alice", email="a@example.com", password="secret")
    form = SendEmailForm(data={"email": "a@example.com"})
    assert form.is_valid()


@pytest.mark.django_db
def test_password_reset_email_form_rejects_unknown_email(db):
    form = SendEmailForm(data={"email": "nobody@example.com"})
    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.django_db
def test_reset_password_confirm_form_mismatch():
    class DummyUser:
        def set_password(self, value):
            self.password = value

        def save(self):
            pass

    form = ResetPasswordConfirmForm(user=DummyUser(), data={"new_password1": "a", "new_password2": "b"})
    assert not form.is_valid()
    assert "new_password2" in form.errors