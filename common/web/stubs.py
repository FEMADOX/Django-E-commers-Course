import datetime
from decimal import Decimal

from cloudinary.models import CloudinaryField

from web.models import Brand, Category, Product


class StubsCategory(Category):
    pk: int
    name: str
    created: datetime.datetime


class StubsBrand(Brand):
    pk: int
    name: str
    fundator: str
    image: CloudinaryField
    created: datetime.datetime


class StubsProduct(Product):
    title: str
    category: StubsCategory
    price: Decimal
    created: datetime.datetime
    updated: datetime.datetime
    description: str
    image: CloudinaryField
    brand: StubsBrand
    weight: int
    dimension: str
    color: str
