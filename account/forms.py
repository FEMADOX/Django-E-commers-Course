from django import forms


class DateInput(forms.DateInput):
    input_type = "date"


class ClientForm(forms.Form):

    SEX_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("N", "Null"),
    )

    dni = forms.CharField(label="DNI", max_length=8, required=True)
    name = forms.CharField(label="Name/s", max_length=200, required=True)
    last_name = forms.CharField(label="Last Name", max_length=200,
                                required=True)
    sex = forms.ChoiceField(label="Sex", choices=SEX_CHOICES, required=True)
    email = forms.EmailField(label="Email", required=True)
    address = forms.CharField(label="Address", required=False,
                              widget=forms.Textarea)
    phone = forms.CharField(label="Phone", max_length=20, required=False)
    birth = forms.DateField(label="Birth Date", required=False,
                            input_formats=["%Y-%m-%d"], widget=DateInput())
