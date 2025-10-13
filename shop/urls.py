from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.login_view, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('profile/', views.profile_view, name='profile'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Cart
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),

    # Order
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/', views.order_success, name='order_success'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:order_id>/', views.my_order_detail, name='my_order_detail'),

    # Admin (manage products)
    path('admin/products/', views.admin_product_list, name='admin_product_list'),
    path('admin/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin/products/edit/<int:pk>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/delete/<int:pk>/', views.admin_product_delete, name='admin_product_delete'),
]
