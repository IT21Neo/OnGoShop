from django.urls import path
from shop import views
from django.contrib.auth import views as auth_views

app_name = 'shop'

urlpatterns = [
    path('', views.login_view, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/category/<int:category_id>/', views.product_list, name='product_list_by_category'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change_form.html', success_url='/profile/'), name='password_change'),
    path('profile/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('cart/', views.view_cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('order/success/', views.order_success, name='order_success'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:order_id>/', views.my_order_detail, name='my_order_detail'),
    path('order/confirm/', views.confirm_order, name='confirm_order'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/products/', views.admin_product_list, name='admin_product_list'),
    path('admin/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin/products/edit/<int:pk>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/delete/<int:pk>/', views.admin_product_delete, name='admin_product_delete'),
    path('admin/categories/', views.admin_category_list, name='admin_category_list'),
    path('admin/categories/add/', views.admin_category_add, name='admin_category_add'),
    path('admin/categories/edit/<int:pk>/', views.admin_category_edit, name='admin_category_edit'),
    path('admin/categories/delete/<int:pk>/', views.admin_category_delete, name='admin_category_delete'),
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/delete/', views.admin_order_delete, name='admin_order_delete'),
    path('admin/orders/<int:order_id>/cancel/', views.admin_order_cancel, name='admin_order_cancel'),
    path('admin/users/', views.admin_user_list, name='admin_user_list'),
    path('admin/users/edit/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),

]
