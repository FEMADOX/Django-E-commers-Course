from account.forms import ClientForm
from account.models import Client, User


def get_or_create_client_form(user: User) -> ClientForm:
    try:
        client = Client.objects.get(user=user)
        client_data = {
            "name": user.username,
            "last_name": user.last_name,
            "email": user.email,
            "dni": client.dni,
            "sex": client.sex,
            "address": client.address,
            "phone": client.phone,
            "birth": client.birth,
        }
    except Client.DoesNotExist:
        client_data = {
            "name": user.username,
            "last_name": user.last_name,
            "email": user.email,
        }
    return ClientForm(client_data)
