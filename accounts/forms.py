from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    student_number = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = User
        fields = ('full_name', 'username', 'email', 'student_number', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.student_number = self.cleaned_data['student_number']
        first_name, last_name = self.cleaned_data['full_name'].split(' ', 1) if ' ' in self.cleaned_data['full_name'] else (self.cleaned_data['full_name'], '')
        user.first_name = first_name
        user.last_name = last_name
        
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))