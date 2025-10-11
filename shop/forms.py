from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from shop.models import Product

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("ชื่อนี้มีอยู่ในระบบแล้ว")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            raise forms.ValidationError("รหัสผ่านทั้งสองช่องต้องตรงกัน")
        return cleaned_data

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Enter username'}),
        label="Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        label="Password"
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = AuthenticationForm(self.request, username=username, password=password)
            if user is None:
                raise forms.ValidationError("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            self.user = user
        return self.cleaned_data

    def get_user(self):
        return self.user

class GuestCheckoutForm(forms.Form):
    receiver_name = forms.CharField(max_length=150, label="ชื่อผู้รับ")
    phone = forms.CharField(max_length=20, label="เบอร์โทรศัพท์")
    address_line = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="ที่อยู่จัดส่ง")
    payment_method = forms.ChoiceField(
        choices=[
            ('transfer', 'โอนเงินผ่านธนาคาร'),
            ('cash', 'เก็บเงินปลายทาง'),
            ('credit_card', 'บัตรเครดิต'),
        ],
        label="วิธีชำระเงิน"
    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }