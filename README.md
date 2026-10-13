# Ecommerce Website with Payment Gateway

A Django-based e-commerce showcase project with a complete checkout flow including PayPal integration and a clean, modern Bootstrap 5 UI.

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

# Load sample data (21 products from fakestoreapi.com)
.venv\Scripts\python.exe manage.py create_data

# Start development server
.venv\Scripts\python.exe manage.py runserver
```

Visit `http://localhost:8000` to view the store.

## Tech Stack

| Component | Version/Details |
|-----------|-----------------|
| **Framework** | Django 6.1 (LTS) |
| **Python** | 3.13 |
| **Database** | SQLite (dev) / PostgreSQL (prod via `DATABASE_URL`) |
| **Payments** | PayPal Checkout Server SDK (`paypal-checkout-serversdk`) |
| **Forms** | django-crispy-forms + crispy-bootstrap5 |
| **Filtering** | django-filter |
| **Testing** | pytest + pytest-django + factory-boy |
| **Frontend** | Bootstrap 5.3 (CDN), Bootstrap Icons, custom minimal CSS |

## Project Structure

```
├── cart/              # Session-based shopping cart + coupons
├── config/            # Django project settings & URLs
├── order/             # Order processing & PayPal integration
├── product/           # Catalog (categories, products, sliders)
├── user_account/      # Custom User model + auth views
├── templates/         # Bootstrap 5 templates (clean, single-window layout)
├── static/            # CSS (app.css), images
│   └── css/app.css    # Minimal custom styles (~150 lines)
├── media/             # Uploaded product/banner images
├── .venv/             # Virtual environment (gitignored)
├── requirements.txt   # Pinned dependencies
├── .env.example       # Environment template
├── .gitignore         # Excludes venv, db.sqlite3, __pycache__, media
├── pytest.ini         # Test configuration
└── README.md          # This file
```

## Key Features

### Cart (`cart/`)
- Session-backed cart (`cart/carts.py`) using `Decimal` for all monetary math
- Coupon system with date ranges, usage limits, minimum spend
- Context processor exposes `cart` to all templates
- `add-to-cart/<id>/` POST, `GET /cart/` for updates, `POST /add-coupon/`

### Products (`product/`)
- Category → Product hierarchy with `featured` flags
- `ImageField` thumbnails stored in `media/products/`
- Slug-based URLs, pagination (8/page), search (`/search-products/`)
- Related products on detail page

### Orders & Payments (`order/`)
- **Server-side PayPal flow**: `POST /checkout/` creates `Order` + `OrderItem`s → calls `OrdersCreateRequest`
- Frontend receives PayPal order ID, renders PayPal Smart Buttons
- `POST /checkout/capture/` captures order server-side, marks `Order.paid=True`, clears cart
- Order history page (`/orders/`) for authenticated users

### Authentication (`user_account/`)
- Custom `User` model (email + username, unique)
- Email-or-username login via custom backend (`EmailAuthenticationBackend`)
- Registration, password change, password reset (class-based, no threading hacks)
- Cart persists across logout

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

## Frontend / UI

**Clean, minimal Bootstrap 5 UI** — fits in a single window, small font sizes (0.875rem base), responsive.

| Page | Description |
|------|-------------|
| **Home** | Hero + featured category cards + featured product grid |
| **Product List** | Responsive grid (2/3/4 cols), pagination, category badges |
| **Product Detail** | Image, price, stock badge, description, add-to-cart with quantity |
| **Category Detail** | Filtered product grid with breadcrumb |
| **Search** | Query param `?key=`, results grid or empty state |
| **Cart** | Table with image, quantity input, subtotal, coupon field, total |
| **Checkout** | Shipping form + PayPal Smart Buttons + order summary sidebar |
| **Orders** | Table with status badges (Delivered/Cancelled/Received), paid indicator |
| **Auth** | Centered cards: Login, Register, Password Reset, Change Password |

### Static Assets
- **CDN**: Bootstrap 5.3 CSS/JS, Bootstrap Icons 1.11
- **Custom**: `static/css/app.css` (~150 lines) — cards, badges, tables, navbar, responsive tweaks
- **No local JS libraries** — all via CDN, zero build step

### Adding Product Images
Upload via admin or place files in `media/products/`. The `Product.thumbnail` is an `ImageField`.

## Sample Data

```bash
.venv\Scripts\python.exe manage.py create_data
```
Loads 21 products across categories (Electronics, Women's Clothing, Men's Clothing, Jewelry) from [fakestoreapi.com](https://fakestoreapi.com).

## Development Commands

```bash
# Run tests (30 tests)
.venv\Scripts\python.exe -m pytest -q

# Check for common issues
.venv\Scripts\python.exe manage.py check --deploy

# Create new migration
.venv\Scripts\python.exe manage.py makemigrations

# Collect static files (production)
.venv\Scripts\python.exe manage.py collectstatic

# Load fake products
.venv\Scripts\python.exe manage.py create_data
```

## PayPal Setup (Showcase)

1. Create a PayPal Developer account
2. Create a **Sandbox** app → get Client ID + Secret
3. Add them to `.env`
4. Frontend loads `https://www.paypal.com/sdk/js?client-id=...&intent=capture`
5. On submit, `Checkout.post()`:
   - Validates form
   - Creates `Order` + `OrderItem`s
   - Calls `create_paypal_order(amount, order_id)` → returns PayPal order ID
   - Returns JSON with `paypal_order_id` to frontend
6. PayPal Smart Buttons render, user approves
7. `onApprove` calls `CaptureOrder` view → captures order, marks paid, clears cart

## Testing

```bash
# Full suite (30 tests)
.venv\Scripts\python.exe -m pytest -q

# By app
.venv\Scripts\python.exe -m pytest cart/tests.py -v
.venv\Scripts\python.exe -m pytest order/tests.py -v
.venv\Scripts\python.exe -m pytest product/tests.py -v
.venv\Scripts\python.exe -m pytest user_account/tests.py -v
```

**Coverage:**
- Cart: add/update/clear/coupon logic with Decimal math
- Checkout: creates order + PayPal order, mocks SDK
- Capture: marks order paid, clears cart
- Products: list, search, detail, category views
- Auth: registration, login, logout, password flows, email backend

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
- Set `PAYPAL_MODE=live` and use live credentials

## Changelog / Upgrade Summary

This project was upgraded from a legacy Django 4.1 codebase with a "Violet" Bootstrap 4 theme.

| Area | Before | After |
|------|--------|-------|
| **Django** | 4.1 | 6.1 (LTS) |
| **Python** | 3.9 | 3.13 |
| **Secrets** | Hardcoded in `settings.py` | `.env` via `django-environ` |
| **Database** | SQLite committed to git | `.gitignore` + `DATABASE_URL` |
| **Product images** | `URLField` (external) | `ImageField(upload_to='products/')` |
| **Money math** | `float()` everywhere | `Decimal` in cart, models, services |
| **Coupons** | Integer discount % | `DecimalField(5,2)` + usage limits + date ranges |
| **Order model** | `paid=True` default, no payment method | `paid=False`, `payment_method`, `paypal_order_id`, `transaction_id` |
| **Checkout** | Hardcoded PayPal amount, no order creation | Full server-side PayPal flow creating `Order` |
| **Auth forms** | `threading.Thread` hack for email | Standard class-based views |
| **Tests** | Empty `tests.py` files | 30 passing pytest tests with mocks |
| **Static assets** | Duplicated in `violet-master/` (88 files) | Single `static/` + CDN Bootstrap 5 |
| **UI Theme** | Violet (Bootstrap 4, jQuery, Owl Carousel, etc.) | Clean Bootstrap 5, minimal CSS |
| **Code quality** | No lint/format/typecheck | `pytest`, `check --deploy`, clean structure |

### UI Overhaul (Latest)
- Removed entire `violet-master/` duplicate directory
- Replaced all templates with clean Bootstrap 5 markup
- New `base.html` with CDN assets, sticky navbar, single-window layout
- New `static/css/app.css` — ~150 lines of minimal utilities
- Product cards, tables, forms, badges all use small fonts (0.875rem)
- Responsive grid: 2 cols mobile, 3 tablet, 4 desktop
- PayPal Smart Buttons integrated in checkout sidebar
- All auth pages centered cards with consistent styling

## License

MIT — for showcase/educational purposes.