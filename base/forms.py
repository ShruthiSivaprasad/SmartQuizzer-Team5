from django import forms
from .models import Profile

class ProfileRegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model = Profile
        fields = ['username', 'password', 'contact', 'gender']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

# Login form 
class ProfileLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

# Admin topic form (with PDF)
class AdminTopicForm(forms.Form):
    topic_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter topic name'})
    )
    sub_topic_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter sub-topic name (optional)'})
    )
    difficulty_level = forms.ChoiceField(
        choices=[('Easy','Easy'),('Medium','Medium'),('Hard','Hard')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text='Upload PDF document (optional)'
    )

# User topic form (without PDF)
class UserTopicForm(forms.Form):
    topic_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter topic name'})
    )
    sub_topic_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter sub-topic name (optional)'})
    )
    difficulty_level = forms.ChoiceField(
        choices=[('Easy','Easy'),('Medium','Medium'),('Hard','Hard')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
