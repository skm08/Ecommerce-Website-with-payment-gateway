from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

User = get_user_model()


class LoginForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=150, widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = User
        fields = ("username", "email", "password", "password2")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with the Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with the Email already exists")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        password2 = cleaned.get("password2")
        if password and password2 and password != password2:
            self.add_error("password2", "Password mismatch")
        return cleaned

    def save(self, commit=True, *args, **kwargs):
        user = self.instance
        user.set_password(self.cleaned_data.get("password"))
        if commit:
            user.save()
        return user


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )
    new_password1 = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )
    new_password2 = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
        self.fields["current_password"].widget.attrs.update(
            {"placeholder": "Type current password"}
        )
        self.fields["new_password1"].widget.attrs.update(
            {"placeholder": "Type new password"}
        )
        self.fields["new_password2"].widget.attrs.update(
            {"placeholder": "Confirm new password"}
        )

    def clean_current_password(self, *args, **kwargs):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Incorrect password")
        return current_password

    def clean(self):
        cleaned = super().clean()
        new_password1 = cleaned.get("new_password1")
        new_password2 = cleaned.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "Password mismatch")
        return cleaned


class SendEmailForm(PasswordResetForm):
    """Plain PasswordResetForm subclass with bootstrap styling.

    Email sending is delegated to Django's built-in class-based flow
    (no more ``threading.Thread`` hack).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("The email is not registered")
        return email


class ResetPasswordConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )
    new_password2 = forms.CharField(
        max_length=150, widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        # Django's PasswordResetConfirmView passes the resolved user under
        # the ``set_password_form`` kwarg in some versions and as ``user``
        # in others; accept either, defaulting to None.
        self.user = kwargs.pop("user", None) or kwargs.pop(
            "set_password_form", None
        )
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned = super().clean()
        new_password1 = cleaned.get("new_password1")
        new_password2 = cleaned.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "Password mismatch")
        return cleaned

    def save(self, commit=True, *args, **kwargs):
        if self.user is None:
            raise ValueError("ResetPasswordConfirmForm requires a user")
        self.user.set_password(self.cleaned_data.get("new_password1"))
        if commit:
            self.user.save()
        return self.user