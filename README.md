# Ecommerce Website with Payment Gateway

A Django-based e-commerce showcase project with a complete checkout flow including PayPal integration.

## Quick Start

```bash
# Create virtual environment
uv venv --python 3.13 .venv

# Install dependencies
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your PayPal credentials and email settings

# Run migrations
.venv\Scripts\python.exe manage.py migrate

# Create superuser (optional)
.venv\Scripts\python.exe manage.py createsuperuser

# Load sample data (optional)
.venv\Scripts\python.exe manage.py create_data

# Start development server
.venv\Scripts\python.exe manage.py runserver
```

Visit `http://localhost:8000` to view the store.

## Tech Stack

| Component | Version/Details |
|-----------|-----------------|
| **Framework** | Django 6.1 (latest LTS) |
| **Python** | 3.13 |
| **Database** | SQLite (dev) / PostgreSQL (prod via `DATABASE_URL`) |
| **Payments** | PayPal Checkout Server SDK (`paypal-checkout-serversdk`) |
| **Forms** | django-crispy-forms + crispy-bootstrap5 |
| **Filtering** | django-filter |
| **Testing** | pytest + pytest-django + factory-boy |
| **Static Assets** | Bootstrap 4, Font Awesome, Owl Carousel |

## Project Structure

```
├── cart/              # Session-based shopping cart + coupons
├── config/            # Django project settings & URLs
├── order/             # Order processing & PayPal integration
├── product/           # Catalog (categories, products, sliders)
├── user_account/      # Custom User model + auth views
├── templates/         # Bootstrap-based templates
├── static/            # CSS, JS, images
├── media/             # Uploaded product/banner images
└── .venv/             # Virtual environment (gitignored)
```

## Key Features

### Cart (`cart/`)
- Session-backed cart (`cart/carts.py`) using `Decimal` for all monetary math
- Coupon system with date ranges, usage limits, minimum spend
- Context processor exposes `cart` to all templates

### Products (`product/`)
- Category → Product hierarchy with `featured` flags
- ImageField for thumbnails (stored in `media/products/`)
- Slug-based URLs, pagination, search

### Orders & Payments (`order/`)
- **Server-side PayPal flow**: `POST /checkout/` creates an `Order` + calls `OrdersCreateRequest`
- Frontend receives PayPal order ID, renders PayPal Smart Buttons
- `POST /checkout/capture/` captures the order server-side, marks `Order.paid=True`
- Order history page for authenticated users

### Authentication (`user_account/`)
- Custom `User` model (email + username, unique)
- Email-or-username login via custom backend
- Registration, password change, password reset (class-based, no threading hacks)

## Environment Variables (`.env`)

```ini
# Django core
SECRET_KEY=your-50-char-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite by default)
DATABASE_URL=sqlite:///db.sqlite3

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_USE_TLS=True
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587

# PayPal (get from https://developer.paypal.com/dashboard/)
PAYPAL_CLIENT_ID=your-sandbox-client-id
PAYPAL_SECRET_ID=your-sandbox-secret
PAYPAL_MODE=sandbox   # or "live"

# Frontend URL for absolute links
FRONTEND_URL=http://localhost:8000
```

## Development Commands

```bash
# Run tests
.venv\Scripts\python.exe -m pytest -q

# Check for common issues
.venv\Scripts\python.exe manage.py check --deploy

# Create new migration
.venv\Scripts\python.exe manage.py makemigrations

# Collect static files (production)
.venv\Scripts\python.exe manage.py collectstatic

# Load fake products from fakestoreapi.com
.venv\Scripts\python.exe manage.py create_data
```

## PayPal Setup (Showcase)

1. Create a PayPal Developer account
2. Create a **Sandbox** app → get Client ID + Secret
3. Add them to `.env`
4. The frontend loads `https://www.paypal.com/sdk/js?client-id=...&intent=capture`
5. On submit, `Checkout.post()`:
   - Validates form
   - Creates `Order` + `OrderItem`s
   - Calls `create_paypal_order(amount, order_id)` → returns PayPal order ID
   - Returns JSON with `paypal_order_id` to frontend
6. PayPal Smart Buttons render, user approves
7. `onApprove` calls `CaptureOrder` view → captures order, marks paid, clears cart

## Testing

```bash
# Full suite (11 + 6 + 17 = 34 tests)
.venv\Scripts\python.exe -m pytest -q

# By app
.venv\Scripts\python.exe -m pytest cart/tests.py -v
.venv\Scripts\python.exe -m pytest order/tests.py -v
.venv\Scripts\python.exe -m pytest product/tests.py -v
.venv\Scripts\python.exe -m pytest user_account/tests.py -v
```

Coverage includes:
- Cart add/update/clear/coupon logic
- Checkout creates order + PayPal order
- Capture marks order paid + clears cart
- Product listing, search, detail views
- Registration, login, logout, password flows

## Deployment Notes

- Set `DEBUG=False` and strong `SECRET_KEY` in production
- Use PostgreSQL: `DATABASE_URL=postgres://user:pass@host/db`
- Enable HTTPS settings:
  ```python
  SECURE_SSL_REDIRECT = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_HSTS_SECONDS = 31536000
  ```
- Run `collectstatic` behind a CDN or nginx
- Configure PayPal webhook for `PAYPAL_WEBHOOK_ID` if needed

## Changelog / Upgrade Summary

This project was upgraded from a legacy Django 4.1 codebase. Key changes:

| Area | Before | After |
|------|--------|-------|
| **Django** | 4.1 | 6.1 (LTS) |
| **Secrets** | Hardcoded in `settings.py` | `.env` via `django-environ` |
| **Database** | SQLite committed to git | `.gitignore` + `DATABASE_URL` |
| **Product images** | `URLField` (external) | `ImageField(upload_to='products/')` |
| **Money math** | `float()` everywhere | `Decimal` in cart, models, services |
| **Coupons** | Integer discount % | `DecimalField(5,2)` + usage limits |
| **Order model** | `paid=True` default, no payment method | `paid=False`, `payment_method`, `paypal_order_id`, `transaction_id` |
| **Checkout** | Hardcoded PayPal amount, no order creation | Full server-side PayPal flow creating `Order` |
| **Auth forms** | `threading.Thread` hack for email | Standard class-based views |
| **Tests** | Empty `tests.py` files | 34 passing pytest tests with mocks |
| **Static assets** | Duplicated in `violet-master/` | Single `static/` directory |
| **Code quality** | No lint/format/typecheck | `pytest`, `check --deploy` |

## License

MIT — for showcase/educational purposes.