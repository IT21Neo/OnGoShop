from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from shop.models import Product, Order, User, Category
from django.contrib.auth.password_validation import validate_password

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

        if password and confirm:
            if password != confirm:
                raise forms.ValidationError("รหัสผ่านทั้งสองช่องต้องตรงกัน")
            
            try:
                validate_password(password)
            except forms.ValidationError as e:
                self.add_error('password', e)

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
            ('transfer', 'Bank Transfer'),
            ('qr_code', 'QR Code Payment'),
            ('cash', 'Cash on Delivery'),
        ],
        label="วิธีชำระเงิน"
    )

class ProductForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="หมวดหมู่สินค้า"
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image_url', 'categories']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': 'ชื่อหมวดหมู่',
            'description': 'คำอธิบาย',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'textarea'}),
            'name': forms.TextInput(attrs={'class': 'input'}),
        }


class OrderStatusForm(forms.ModelForm):
    
    class Meta:
        model = Order
        fields = ['status']
        labels = {
            'status': "สถานะคำสั่งซื้อ"
        }
        widgets = {
            'status': forms.Select(attrs={'class': 'select is-fullwidth'})
        }

class UserRoleForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('customer', 'ลูกค้าทั่วไป'),
        ('admin', 'ผู้ดูแลระบบ'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="บทบาทผู้ใช้",
        widget=forms.Select(attrs={'class': 'select is-fullwidth'})
    )
    
    is_staff = forms.BooleanField(
        required=False, 
        label="สิทธิ์ Staff (เข้าหน้า Admin)"
    )

    class Meta:
        model = User
        fields = ['role', 'is_staff']

class ProfileForm(forms.ModelForm):
    address_line = forms.CharField(
        label="ที่อยู่สำหรับจัดส่ง", 
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'textarea'}), 
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture']
        labels = {
            'first_name': 'ชื่อจริง (ผู้รับ)',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
            'phone': 'เบอร์โทรศัพท์',
            'profile_picture': 'URL รูปโปรไฟล์',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input'}),
            'last_name': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'phone': forms.TextInput(attrs={'class': 'input', 'placeholder': '0812345678'}),
            'profile_picture': forms.TextInput(attrs={'class': 'input', 'placeholder': 'https://example.com/image.png'}),
        }