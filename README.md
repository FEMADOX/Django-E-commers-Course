# Django E-commerce Course

A full-featured e-commerce web application built with Django, featuring user authentication, shopping cart functionality, order management, and payment processing.

## 🚀 Features

- **User Management**: Registration, login, logout, and account activation
- **Product Catalog**: Browse products with categories, brands, and detailed information
- **Shopping Cart**: Add, remove, and manage items in your cart
- **Order Processing**: Complete order workflow with status tracking
- **Payment Integration**: Secure payment processing
- **Responsive Design**: Mobile-friendly interface
- **Admin Panel**: Django admin for managing products, orders, and users

## 📁 Project Structure

```bash
Django-E-commers-Course/
├── account/          # User authentication and account management
├── cart/             # Shopping cart functionality
├── common/           # Shared utilities and stubs
├── edshop/           # Main Django project settings
├── media/            # User uploaded files
├── order/            # Order processing and management
├── payment/          # Payment processing
├── static/           # Static files (CSS, JS, images)
├── templates/        # HTML templates
├── tests/            # Test files
├── web/              # Main web application (products, categories)
├── manage.py         # Django management script
├── pyproject.toml    # Project dependencies and configuration
└── README.md         # This file
```

## 🛠️ Technologies Used

- **Backend**: Django (Python)
- **Database**: Postgres
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with Font Awesome icons
- **Development Tools**:
  - Ruff (linting and formatting)
  - Pre-commit hooks
  - pytest (testing)
  - uv (dependency management)

## 📋 Prerequisites

- Python 3.11+
- uv (recommended) or pip for dependency management

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/FEMADOX/Django-E-commers-Course.git
cd Django-E-commers-Course
```

### 2. Install dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3.1 Set up environment variables

Create a `.env` file in the project root with the following configuration:

```bash
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGIN_WHITELIST=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
LOCAL_DATABASE=True

# Payment Processing
STRIPE_API=your-stripe-api-key

# Email Configuration
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password

# Database Configuration
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

# Cloudinary (Media Storage)
CLOUD_NAME=your-cloudinary-name
CLOUD_API_KEY=your-cloudinary-api-key
CLOUD_API_SECRET=your-cloudinary-api-secret
```

> **Note**: Never commit your `.env` file to version control. Add it to your `.gitignore` file.

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to see the application.

## 🧪 Testing

Run the test suite:

```bash
python run_tests.py
# or
pytest
```

## 🔧 Development

### Code Quality

This project uses Ruff for linting and formatting:

```bash
python run_ruff.py
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pre-commit install
```

## 📱 Application Modules

### Account (`account/`)

- User registration and authentication
- Account activation via email
- User profile management
- Login/logout functionality

### Cart (`cart/`)

- Session-based shopping cart
- Add/remove products
- Quantity management
- Price calculations

### Web (`web/`)

- Product catalog
- Category and brand management
- Product search and filtering
- Product detail pages

### Order (`order/`)

- Order creation and management
- Order status tracking
- Order history

### Payment (`payment/`)

- Payment processing integration
- Transaction management

## 🎨 Frontend

The application uses a responsive design with:

- Custom CSS styling
- Font Awesome icons
- Google Fonts (Montserrat, Open Sans)
- Mobile-first approach

## 📄 License

This project is created for educational purposes as part of a Django e-commerce course.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions and support, please open an issue on GitHub.

## 🔗 Links

- [Project Repository](https://github.com/FEMADOX/Django-E-commers-Course)
- [Django Documentation](https://docs.djangoproject.com/)

---

Built with ❤️ using Django
