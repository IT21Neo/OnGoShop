from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='customer')
    profile_picture = models.CharField(max_length=255, blank=True, null=True, help_text="URL to profile picture")

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    stock = models.IntegerField(default=0)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name="products", blank=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user.username if self.user else 'Guest'})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอชำระเงิน'),
        ('paid', 'ชำระเงินแล้ว'),
        ('shipping', 'กำลังจัดส่ง'),
        ('delivered', 'จัดส่งสำเร็จ'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.PositiveIntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

class Payment(models.Model):
    PAYMENT_METHODS = [('credit_card','credit_card'), ('transfer','transfer'), ('cash','cash')]
    PAYMENT_STATUS = [('pending','รอการยืนยัน'), ('success','สำเร็จแล้ว'), ('cancelled','ยกเลิก')]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField()
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    receiver_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.receiver_name} - {self.address_line}"

class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.action}'

    class Meta:
        ordering = ['-timestamp']
