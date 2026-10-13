"""Tests for product listing, search and category detail views."""
from decimal import Decimal

import pytest
from django.test import Client

from product.models import Category, Product


@pytest.fixture
def category(db):
    return Category.objects.create(title="Electronics", slug="electronics", featured=True)


@pytest.fixture
def product(category):
    return Product.objects.create(
        category=category,
        title="Widget",
        slug="widget",
        price="20.00",
        thumbnail="https://example.com/widget.jpg",
        featured=True,
    )


@pytest.mark.django_db
def test_home_page_renders(client, product):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Widget" in response.content


@pytest.mark.django_db
def test_product_list_paginates(client, category):
    for i in range(10):
        Product.objects.create(
            category=category,
            title=f"Product {i}",
            slug=f"product-{i}",
            price="10.00",
            thumbnail="https://example.com/p.jpg",
        )
    response = client.get("/product-list/")
    assert response.status_code == 200
    # paginate_by = 8 -> first page shows 8 items.
    assert response.context["paginator"].count == 10


@pytest.mark.django_db
def test_product_detail_renders(client, product):
    response = client.get(f"/product-details/{product.slug}/")
    assert response.status_code == 200
    assert b"Widget" in response.content


@pytest.mark.django_db
def test_category_detail_lists_products(client, category, product):
    response = client.get(f"/category-details/{category.slug}/")
    assert response.status_code == 200
    assert b"Widget" in response.content


@pytest.mark.django_db
def test_search_products_finds_match(client, category, product):
    response = client.get("/search-products/", {"key": "Widget"})
    assert response.status_code == 200
    assert b"Widget" in response.content


@pytest.mark.django_db
def test_search_products_no_match(client, category, product):
    response = client.get("/search-products/", {"key": "zzz-no-match"})
    assert response.status_code == 200
    assert b"Widget" not in response.content