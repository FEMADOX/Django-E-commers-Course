import datetime

from django.contrib.auth.models import User

from account.models import Client


class StubsClient(Client):
    user: User
    dni: str
    sex: str
    phone: str
    birth: datetime.date
    address: str
    created: datetime.date
    updated: datetime.date
