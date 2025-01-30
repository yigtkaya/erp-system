from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from erp_core.models import User, UserProfile, Department

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    employee_id = forms.CharField(max_length=50, required=True)
    role = forms.ChoiceField(choices=User.role.field.choices)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'department', 'employee_id']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if UserProfile.objects.filter(employee_id=employee_id).exists():
            raise ValidationError("Employee ID already exists")
        return employee_id

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['department', 'phone_number', 'employee_id']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'}) 