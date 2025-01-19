# import pytest
# from django.conf import settings


# @pytest.fixture(scope="session")
# def django_db_setup():
#     settings.configure(
#         INSTALLED_APPS=[
#             "django.contrib.auth",
#             "django.contrib.contenttypes",
#             "django.contrib.sessions",
#             "django.contrib.admin",
#             "django.contrib.messages",
#             "django.contrib.staticfiles",
#             "stripe",
#             "web",
#             "account",
#             "cart",
#             "payment",
#             "order",
#         ],
#         DATABASES={
#             "default": {
#                 "ENGINE": "django.db.backends.sqlite3",
#                 "NAME": ":memory:",
#             }
#         },
#         # Add other settings as needed
#     )
#     import django

#     django.setup()
