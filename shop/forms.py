from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from shop.models import Product

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="รหัสผ่าน")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="ยืนยันรหัสผ่าน")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        cpw = cleaned_data.get("confirm_password")
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("รหัสผ่านไม่ตรงกัน")
        return cleaned_data

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="ชื่อผู้ใช้")
    password = forms.CharField(widget=forms.PasswordInput, label="รหัสผ่าน")

class GuestCheckoutForm(forms.Form):
    receiver_name = forms.CharField(max_length=150, label="ชื่อผู้รับ")
    phone = forms.CharField(max_length=20, label="เบอร์โทรศัพท์")
    address_line = forms.CharField(widget=forms.Textarea, label="ที่อยู่จัดส่ง")
    payment_method = forms.ChoiceField(
        choices=[('transfer', 'โอนเงิน'), ('cash', 'ชำระปลายทาง')],
        label="วิธีการชำระเงิน"
    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image_url']