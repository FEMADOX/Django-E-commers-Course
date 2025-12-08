# Django E-Commerce Copilot Instructions

## Project Architecture

This is a Django 5.1+ e-commerce application with modular app structure:
- **account/**: User authentication with custom email-based backend (`AccountBackend`) + Client profile extension
- **web/**: Product catalog (Product, Category, Brand models with CloudinaryField)
- **cart/**: Session-based shopping cart (`cart.cart.Cart` class, not a model)
- **order/**: Order processing (Order + OrderDetail models)
- **payment/**: Stripe payment integration
- **common/**: Shared utilities (e.g., `get_or_create_client_form`)

### Key Architectural Patterns

**Custom Authentication Backend**: Email login instead of username. See `account/backends.py`:
```python
# Users authenticate with email, not username
user = user_model.objects.get(email=email)
```

**Session-Based Cart**: Cart data lives in Django sessions (`request.session['cart']`), not database. See `cart/cart.py`:
```python
self.cart = self.session.get("cart", {})  # Dictionary stored in session
```

**Client Profile Pattern**: Django's User model extended via OneToOne with `account.models.Client` (DNI, phone, address).

**Email Activation Workflow**: Registration → inactive User → email with activation link → user activates → login.
- Token: SHA256 hash of email
- UID: base64-encoded email
- See `account/emails.py` and `account/views.AccountActivationView`

**CSS styling**: Like TailwindCSS, using Mobile First Philosophy.
- Using SCSS syntax for nested styles in CSS files.

## Development Workflow

### Environment Setup
```bash
# Install dependencies (uses uv, not pip/poetry)
uv sync

# Environment variables (see .env.example)
DJANGO_SECRET_KEY, DEBUG, LOCAL_DATABASE=True, STRIPE_API, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET  # Cloudinary for images

# Database: SQLite by default, PostgreSQL if LOCAL_DATABASE=False
python manage.py migrate
python manage.py runserver
```

### Testing
```bash
# Run tests with pytest-django (configured in pyproject.toml)
uv run pytest -n auto  # Parallel execution with pytest-xdist

# Test structure: tests/<app_name>/test_*.py
# Fixtures in tests/<app_name>/conftest.py
# Markers: @pytest.mark.unit, @pytest.mark.integration
```

### Linting & Formatting
```bash
# Ruff with strict Django rules (see pyproject.toml [tool.ruff])
uv run ruff check --fix .
uv run ruff format .

# Or use convenience script
uv run python run_ruff.py

# Pre-commit hooks run tests + linting automatically
```

## Code Conventions

### Type Annotations (Required)
All functions must have full type hints (enforced by Ruff ANN* rules):
```python
from __future__ import annotations  # Always at top
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # Runtime imports only for type checking
    from django.http import HttpRequest
```

### View Patterns
- **CBVs preferred**: Use `LoginRequiredMixin`, `TemplateView`, `UpdateView`
- **GET redirects**: `AddProductCartView.get()` redirects to POST for login flow compatibility
- **Form handling**: Return `HttpResponseRedirect` on success, re-render with form on validation errors

### Model Patterns
- **Indexes**: All foreign keys and common query fields have explicit `models.Index`
- **CloudinaryField**: Default images with transformations (300x300, auto quality/format)
- **Ordering**: `-created` default ordering on all models with timestamps
- **Choice Fields**: Use tuples, not Enums (e.g., `Order.STATUS_CHOICES`)

### Testing Patterns
- **Fixtures**: Centralized in `conftest.py` per app (e.g., `authenticated_user`, `client_data`)
- **Parametrize**: Use `tests/common/parametrizes.py` constants (PARAM_INVALID_EMAIL, etc.)
- **Status codes**: Use `tests/common/status.py` constants (HTTP_200_OK, etc.)
- **Integration tests**: Test full workflows (signup → activation → login) in `test_integration.py`

### Django Settings
- **Environment-based security**: CSRF/SSL/HSTS settings differ by `ENVIRONMENT` (production/development)
- **Static files**: WhiteNoise for static file serving (no Cloudinary for static)
- **Authentication**: Two backends in `AUTHENTICATION_BACKENDS` (ModelBackend + AccountBackend)
- **Crispy Forms**: Bootstrap 5 templates

## Critical Dependencies

- **django-environ**: All config from .env (SECRET_KEY, DATABASE_URL if not LOCAL_DATABASE)
- **cloudinary**: Product/Brand images stored in Cloudinary folders (Django-E-commers/media/)
- **stripe**: Payment processing (API key in settings.STRIPE_API)
- **phonenumber-field**: Client phone validation
- **whitenoise**: Static file compression/caching

## Common Gotchas

1. **Cart persistence**: Cart clears on logout (session-based). Use `restore_order_pending()` to recover from Order.
2. **Email activation**: Token expires when User.is_active changes (invalidated by Django's token generator).
3. **Cloudinary URLs**: Handle both CloudinaryField objects and string URLs in cart:
   ```python
   image_url = product.image.url if hasattr(product.image, 'url') else str(product.image)
   ```
4. **Migration exclusions**: Migrations excluded from linting/formatting (see pyproject.toml)
5. **Test database**: pytest-django uses separate test database automatically

## Key Files Reference

- `edshop/settings.py`: Environment-based configuration, custom backends
- `cart/cart.py`: Session-based cart implementation (not a model!)
- `account/backends.py`: Email authentication backend
- `account/emails.py`: Custom email sending with template rendering
- `common/views/client.py`: Shared client form logic
- `pyproject.toml`: Ruff rules, pytest config, dependencies
