from django import forms

from account.models import Client


class DateInput(forms.DateInput):
    input_type = "date"


class ClientForm(forms.ModelForm):
    SEX_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("N", "Null"),
    )

    dni = forms.CharField(label="DNI", max_length=8, required=False)
    name = forms.CharField(label="Name/s", max_length=100, required=True)
    last_name = forms.CharField(label="Last Name", max_length=100, required=False)
    sex = forms.ChoiceField(label="Sex", choices=SEX_CHOICES, required=False)
    email = forms.EmailField(label="Email", required=True)
    address = forms.CharField(label="Address", required=False, widget=forms.Textarea)
    phone = forms.CharField(label="Phone", max_length=20, required=False)
    birth = forms.DateField(
        label="Birth Date",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=DateInput(),
    )

    class Meta:
        model = Client
        fields = [
            "dni",
            "name",
            "last_name",
            "sex",
            "email",
            "address",
            "phone",
            "birth",
        ]
