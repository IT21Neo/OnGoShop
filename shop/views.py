from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import login, logout
from django.db.models import Sum
from shop.forms import RegisterForm, AuthenticationForm, ProductForm, GuestCheckoutForm, OrderStatusForm, UserRoleForm, ProfileForm, CategoryForm
from shop.models import User, Product, Category, Cart, CartItem, Order, OrderItem, Payment, Address, ActivityLog

def admin_check(user):
    return user.is_authenticated and (getattr(user, 'role', '') in ['admin', 'owner'] or user.is_staff or user.is_superuser)

def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('shop:login')

    if not admin_check(request.user):
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        return redirect('shop:product_list')

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(status='paid').aggregate(total=Sum('total_price'))['total'] or 0
    activity_logs = ActivityLog.objects.select_related('user').order_by('-timestamp')[:10]

    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'activity_logs': activity_logs,
    })

def admin_product_list(request):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    products = Product.objects.all()
    return render(request, 'admin_product_list.html', {'products': products})

def log_activity(user, action, category="ทั่วไป"):
    try:
        ActivityLog.objects.create(user=user, action=action, category=category)
    except Exception as e:
        print(f"[ActivityLog] Error: {e}")

def admin_product_add(request):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            log_activity(request.user, f"เพิ่มสินค้าใหม่: {product.name}", "จัดการสินค้า")
            messages.success(request, "เพิ่มสินค้าใหม่เรียบร้อยแล้ว!")
            return redirect('shop:admin_product_list')
        else:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
    else:
        form = ProductForm()

    return render(request, 'admin_product_form.html', {'form': form, 'title': 'เพิ่มสินค้า'})

def admin_product_edit(request, pk):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, "ไม่พบสินค้านี้")
        return redirect('shop:admin_product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"แก้ไขสินค้า #{product.id}: {product.name}", "จัดการสินค้า")
            messages.success(request, "แก้ไขสินค้าเรียบร้อยแล้ว!")
            return redirect('shop:admin_product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'admin_product_form.html', {'form': form, 'title': 'แก้ไขสินค้า'})

def admin_product_delete(request, pk):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, "ไม่พบสินค้านี้")
        return redirect('shop:admin_product_list')

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        log_activity(request.user, f"ลบสินค้า #{pk}: {product_name}", "จัดการสินค้า")
        messages.info(request, "ลบสินค้าเรียบร้อยแล้ว")
        return redirect('shop:admin_product_list')

    return render(request, 'admin_product_delete.html', {'product': product})

def admin_category_list(request):
    if not admin_check(request.user):
        return redirect('shop:login')

    categories = Category.objects.all()
    return render(request, 'admin_category_list.html', {'categories': categories})

def admin_category_add(request):
    if not admin_check(request.user):
        return redirect('shop:login')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            log_activity(request.user, f"เพิ่มหมวดหมู่: '{category.name}'", "จัดการหมวดหมู่")
            messages.success(request, "เพิ่มหมวดหมู่ใหม่เรียบร้อยแล้ว!")
            return redirect('shop:admin_category_list')
    else:
        form = CategoryForm()

    return render(request, 'admin_category_form.html', {'form': form, 'title': 'เพิ่มหมวดหมู่ใหม่'})

def admin_category_edit(request, pk):
    if not admin_check(request.user):
        return redirect('shop:login')

    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        messages.error(request, "ไม่พบหมวดหมู่นี้")
        return redirect('shop:admin_category_list')

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"แก้ไขหมวดหมู่: '{category.name}'", "จัดการหมวดหมู่")
            messages.success(request, "แก้ไขข้อมูลหมวดหมู่เรียบร้อยแล้ว")
            return redirect('shop:admin_category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'admin_category_form.html', {'form': form, 'title': f"แก้ไข: {category.name}"})

def admin_category_delete(request, pk):
    if not admin_check(request.user):
        return redirect('shop:login')

    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        messages.error(request, "ไม่พบหมวดหมู่นี้")
        return redirect('shop:admin_category_list')

    if request.method == 'POST':
        category_name = category.name
        category.delete()
        log_activity(request.user, f"ลบหมวดหมู่: '{category_name}'", "จัดการหมวดหมู่")
        messages.info(request, f"ลบหมวดหมู่ '{category_name}' เรียบร้อยแล้ว")
        return redirect('shop:admin_category_list')
        
    return render(request, 'admin_category_delete.html', {'category': category})

def admin_order_list(request):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')
    return render(request, 'admin_order_list.html', {'orders': orders})

def admin_order_detail(request, order_id):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    try:
        order = Order.objects.prefetch_related('items__product', 'payments').get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, "ไม่พบคำสั่งซื้อนี้")
        return redirect('shop:admin_order_list')

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            new_status = form.cleaned_data.get('status')
            log_activity(request.user, f"อัปเดตสถานะคำสั่งซื้อ #{order.id} เป็น '{new_status}'", "จัดการคำสั่งซื้อ")
            form.save()
            messages.success(request, f"อัพเดตสถานะ #{order.id} เรียบร้อยแล้ว")
            return redirect('shop:admin_order_detail', order_id=order.id)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, 'admin_order_detail.html', {'order': order, 'form': form})

def admin_order_delete(request, order_id):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, "ไม่พบคำสั่งซื้อนี้")
        return redirect('shop:admin_order_list')

    if request.method == 'POST':
        order.delete()
        messages.success(request, f"ลบคำสั่งซื้อ #{order_id} เรียบร้อยแล้ว")
        return redirect('shop:admin_order_list')

    messages.warning(request, "การลบคำสั่งซื้อจำเป็นต้องส่งคำขอแบบ POST เท่านั้น")
    return redirect('shop:admin_order_list')


def admin_order_cancel(request, order_id):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'cancelled'
            order.save()
            log_activity(request.user, f"ยกเลิกคำสั่งซื้อ #{order.id}", "จัดการคำสั่งซื้อ")
            messages.info(request, f"ยกเลิกคำสั่งซื้อ #{order.id}")
        except Order.DoesNotExist:
            messages.error(request, "ไม่พบคำสั่งซื้อนี้")
    return redirect('shop:admin_order_list')

def admin_user_list(request):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_user_list.html', {'users': users})

def admin_user_edit(request, user_id):
    if not request.user.is_authenticated or not admin_check(request.user):
        return redirect('shop:login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "ไม่พบผู้ใช้")
        return redirect('shop:admin_user_list')

    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"อัพเดตบทบาทของผู้ใช้ {user.username}", "จัดการสมาชิก")
            messages.success(request, f"อัพเดตผู้ใช้ {user.username} แล้ว")
            return redirect('shop:admin_user_list')

    else:
        form = UserRoleForm(instance=user)

    return render(request, 'admin_user_edit.html', {'user_obj': user, 'form': form})


# authen part
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data.get('password'))
            user.save()
            messages.success(request, "สมัครสมาชิกสำเร็จ! โปรดเข้าสู่ระบบ")
            return redirect('shop:login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if admin_check(user):
                return redirect('shop:admin_dashboard')
            return redirect('shop:product_list')
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "ออกจากระบบแล้ว")
    return redirect('shop:product_list')



# Profile part
def profile_view(request):
    """แสดงหน้าข้อมูลโปรไฟล์ของผู้ใช้"""
    if not request.user.is_authenticated:
        return redirect('shop:login')

    if admin_check(request.user):
        return render(request, 'admin_profile.html', {'user': request.user})
    else:
        return render(request, 'profile.html', {'user': request.user})


def profile_edit(request):
    """แก้ไขข้อมูลโปรไฟล์"""
    if not request.user.is_authenticated:
        return redirect('shop:login')

    user = request.user
    try:
        user_address = Address.objects.get(user=user)
    except Address.DoesNotExist:
        user_address = None

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            Address.objects.update_or_create(
                user=user,
                defaults={
                    'receiver_name': f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}".strip(),
                    'phone': form.cleaned_data['phone'],
                    'address_line': form.cleaned_data['address_line']
                }
            )
            messages.success(request, "อัปเดตโปรไฟล์เรียบร้อยแล้ว!")
            return redirect('shop:profile')
    else:
        initial_data = {}
        if user_address:
            initial_data['address_line'] = user_address.address_line
        form = ProfileForm(instance=user, initial=initial_data)

    template_name = 'admin_profile_edit.html' if admin_check(user) else 'profile_edit.html'
    return render(request, template_name, {'form': form})



# Product part
def product_list(request, category_id=None):
    products = Product.objects.all()
    categories = Category.objects.all()
    current_category = None

    if category_id:
        try:
            current_category = Category.objects.get(id=category_id)
            products = products.filter(categories=current_category)
        except Category.DoesNotExist:
            messages.error(request, "ไม่พบหมวดหมู่สินค้านี้")
            return redirect('shop:product_list')

    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(name__icontains=search_query)

    sort_option = request.GET.get('sort')
    if sort_option == 'price_low':
        products = products.order_by('price')
    elif sort_option == 'price_high':
        products = products.order_by('-price')
    elif sort_option == 'newest':
        products = products.order_by('-id')

    recommended_products = Product.objects.order_by('-id')[:4]

    context = {
        'products': products,
        'categories': categories,
        'recommended_products': recommended_products,
        'current_category': current_category,
    }
    return render(request, 'product_list.html', context)

def product_detail(request, pk):
    try:
        product = Product.objects.get(id=pk)
    except Product.DoesNotExist:
        messages.error(request, "❌ ไม่พบสินค้านี้")
        return redirect('shop:product_list')

    return render(request, 'product_detail.html', {'product': product})

# cart part
def _get_cart(request):
    """คืนค่า cart ของ user หรือ session ปัจจุบัน"""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def add_to_cart(request):
    if request.method != "POST":
        return redirect("shop:product_list")

    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "❌ ไม่พบสินค้าที่เลือก")
        return redirect("shop:product_list")

    cart = _get_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": quantity}
    )

    if not created:
        item.quantity += quantity
        item.save()

    messages.success(request, f"เพิ่ม {product.name} ลงในตะกร้าแล้ว!")
    return redirect("shop:product_list")

def view_cart(request):
    if not request.user.is_authenticated:
        messages.warning(request, "กรุณาเข้าสู่ระบบก่อนดูตะกร้าสินค้า")
        return redirect("shop:login")

    cart = _get_cart(request)
    items = cart.items.select_related("product")

    for item in items:
        item.subtotal = item.product.price * item.quantity

    total = sum(item.subtotal for item in items)

    return render(request, "cart.html", {"items": items, "total": total})

def remove_from_cart(request):
    if not request.user.is_authenticated:
        return redirect("shop:login")

    if request.method == "POST":
        product_id = request.POST.get("product_id")
        cart = _get_cart(request)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        messages.info(request, "นำสินค้าออกจากตะกร้าแล้ว")

    return redirect("shop:cart")

def update_cart(request):
    if not request.user.is_authenticated:
        return redirect("shop:login")

    if request.method != "POST":
        return redirect("shop:cart")

    product_id = request.POST.get("product_id")
    action = request.POST.get("action")

    cart = _get_cart(request)

    try:
        item = CartItem.objects.get(cart=cart, product_id=product_id)
    except CartItem.DoesNotExist:
        messages.error(request, "ไม่พบสินค้าในตะกร้า")
        return redirect("shop:cart")

    if action == "increase":
        item.quantity += 1
    elif action == "decrease":
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
            messages.info(request, "นำสินค้าออกจากตะกร้าแล้ว")
            return redirect("shop:cart")

    item.save()
    return redirect("shop:cart")


# checkout Part

@transaction.atomic
def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request, "กรุณาเข้าสู่ระบบก่อนสั่งซื้อสินค้า")
        return redirect("shop:login")

    cart = _get_cart(request)

    if not cart.items.exists():
        messages.warning(request, "ตะกร้าสินค้าของคุณว่างเปล่า")
        return redirect("shop:product_list")

    user = request.user
    initial_data = {
        'receiver_name': user.get_full_name(),
        'phone': getattr(user, 'phone', ''),
    }

    try:
        address = Address.objects.get(user=user)
        initial_data['address_line'] = address.address_line
    except Address.DoesNotExist:
        pass

    if request.method == 'POST':
        form = GuestCheckoutForm(request.POST)
        if form.is_valid():
            request.session['checkout_info'] = form.cleaned_data
            return redirect('shop:confirm_order')
    else:
        form = GuestCheckoutForm(initial=initial_data)

    return render(request, 'checkout.html', {'form': form})

@transaction.atomic
def confirm_order(request):
    if not request.user.is_authenticated:
        return redirect("shop:login")

    checkout_info = request.session.get('checkout_info')
    cart = _get_cart(request)

    if not checkout_info or not cart.items.exists():
        messages.error(request, "ข้อมูลการสั่งซื้อไม่สมบูรณ์ กรุณาเริ่มใหม่อีกครั้ง")
        return redirect('shop:checkout')

    items = list(cart.items.select_related('product'))
    total_price = sum(item.quantity * item.product.price for item in items)

    if request.method == 'POST':
        try:
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                status='pending'
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price
                )
                product = item.product
                product.stock = max(0, product.stock - item.quantity)
                product.save()

            Payment.objects.create(
                order=order,
                amount=total_price,
                method=checkout_info['payment_method'],
                status='pending'
            )

            cart.items.all().delete()
            if 'checkout_info' in request.session:
                del request.session['checkout_info']

            messages.success(request, "ยืนยันคำสั่งซื้อสำเร็จแล้ว!")
            return redirect('shop:order_success')

        except Exception as e:
            messages.error(request, f"เกิดข้อผิดพลาด: {e}")
            return redirect('shop:checkout')

    return render(request, 'confirm_order.html', {
        'checkout_info': checkout_info,
        'cart_items': items,
        'total_price': total_price
    })


# Order Part

def my_orders(request):
    """แสดงคำสั่งซื้อทั้งหมดของผู้ใช้"""
    if not request.user.is_authenticated:
        return redirect('shop:login')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})

def my_order_detail(request, order_id):
    """แสดงรายละเอียดคำสั่งซื้อแต่ละรายการ"""
    if not request.user.is_authenticated:
        return redirect('shop:login')

    try:
        order = Order.objects.prefetch_related('items__product').get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, "ไม่พบคำสั่งซื้อนี้")
        return redirect('shop:my_orders')

    return render(request, 'my_order_detail.html', {'order': order})


def order_success(request):
    return render(request, 'order_success.html')
