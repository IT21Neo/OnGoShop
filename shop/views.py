from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.conf import settings
from django.db.models import Q
from shop.forms import RegisterForm, AuthenticationForm, ProductForm, GuestCheckoutForm, OrderStatusForm, UserRoleForm
from shop.models import User, Product, Cart, CartItem, Order, OrderItem, Payment


# ตรวจสิทธิ์ admin
def admin_check(user):
    return user.is_authenticated and (getattr(user, 'role', '') in ['admin', 'owner'] or user.is_staff or user.is_superuser)

@login_required
def admin_product_list(request):
    if request.user.role != 'admin':
        return redirect('shop:product_list')

    products = Product.objects.all()
    return render(request, 'shop/admin_product_list.html', {
        'products': products,
    })

@user_passes_test(admin_check, login_url='shop:login')
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มสินค้าใหม่เรียบร้อยแล้ว!")
            return redirect('shop:admin_product_list')
        else:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
    else:
        form = ProductForm()
    return render(request, 'admin_product_form.html', {'form': form, 'title': 'เพิ่มสินค้า'})

@user_passes_test(admin_check, login_url='shop:login')
def admin_product_edit(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, "ไม่พบสินค้านี้")
        return redirect('shop:admin_product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขสินค้าเรียบร้อยแล้ว!")
            return redirect('shop:admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_product_form.html', {'form': form, 'title': 'แก้ไขสินค้า'})

@user_passes_test(admin_check, login_url='shop:login')
def admin_product_delete(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        messages.error(request, "ไม่พบสินค้านี้")
        return redirect('shop:admin_product_list')

    if request.method == 'POST':
        product.delete()
        messages.info(request, "ลบสินค้าเรียบร้อยแล้ว")
        return redirect('shop:admin_product_list')

    return render(request, 'admin_product_delete.html', {'product': product})

@user_passes_test(admin_check, login_url='shop:login')
def admin_order_list(request):
    """แสดงรายการคำสั่งซื้อทั้งหมด (admin)"""
    orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')
    return render(request, 'admin_order_list.html', {'orders': orders})

@user_passes_test(admin_check, login_url='shop:login')
def admin_order_detail(request, order_id):
    """รายละเอียดคำสั่งซื้อ และฟอร์มเปลี่ยนสถานะ"""
    order = get_object_or_404(Order.objects.prefetch_related('items__product', 'payments'), id=order_id)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"อัพเดตสถานะคำสั่งซื้อ #{order.id} เรียบร้อยแล้ว")
            return redirect('shop:admin_order_detail', order_id=order.id)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, 'admin_order_detail.html', {'order': order, 'form': form})

@user_passes_test(admin_check, login_url='shop:login')
@require_http_methods(["POST"])
def admin_order_cancel(request, order_id):
    """ยกเลิกคำสั่งซื้อโดย admin"""
    order = get_object_or_404(Order, id=order_id)
    order.status = 'cancelled'
    order.save()
    messages.info(request, f"ยกเลิกคำสั่งซื้อ #{order.id}")
    return redirect('shop:admin_order_detail', order_id=order.id)

@login_required
def admin_user_list(request):
    if request.user.role != 'admin':
        return redirect('shop:product_list')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'shop/admin_user_list.html', {'users': users})


@user_passes_test(admin_check, login_url='shop:login')
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"อัพเดตข้อมูลผู้ใช้ {user.username} เรียบร้อย")
            return redirect('shop:admin_user_list')
    else:
        form = UserRoleForm(instance=user)
    return render(request, 'admin_user_edit.html', {'user_obj': user, 'form': form})


# สมัครสมาชิก
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            messages.success(request, "สมัครสมาชิกสำเร็จแล้ว! โปรดเข้าสู่ระบบ")
            return redirect('shop:login')
        else:
            # form invalid -> render with errors
            messages.error(request, "เกิดข้อผิดพลาดในการสมัครสมาชิก กรุณาตรวจสอบข้อมูล")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# เข้าสู่ระบบ
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)
            
            messages.success(request, f"ยินดีต้อนรับ {user.username}!")
            return redirect('shop:product_list')
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# ออกจากระบบ
def logout_view(request):
    logout(request)
    messages.info(request, "ออกจากระบบเรียบร้อยแล้ว")
    return redirect('shop:product_list')

# แสดงสินค้าทั้งหมด
def product_list(request):
    """หน้าแสดงสินค้าทั้งหมด + ค้นหา + เรียงลำดับ + เพิ่มลงตะกร้า"""
    products = Product.objects.all().order_by('-id')

    # 🔍 ค้นหาสินค้า
    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # 🔽 เรียงลำดับสินค้า
    sort = request.GET.get('sort')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-id')
    elif sort == 'oldest':
        products = products.order_by('id')

    # 🛒 เพิ่มสินค้าลงตะกร้า
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if request.user.is_authenticated:
            product = Product.objects.get(id=product_id)
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            messages.success(request, f"เพิ่ม {product.name} ลงในตะกร้าแล้ว!")
        else:
            messages.error(request, "กรุณาเข้าสู่ระบบก่อนเพิ่มสินค้าลงตะกร้า")
            return redirect('shop:login')
        return redirect('shop:product_list')

    return render(request, 'product_list.html', {'products': products})

# แสดงรายละเอียดสินค้า
def product_detail(request, pk):
    try:
        product = Product.objects.get(id=pk)
    except Product.DoesNotExist:
        messages.error(request, "❌ ไม่พบสินค้านี้")
        return redirect('shop:product_list')

    return render(request, 'product_detail.html', {'product': product})

# ฟังก์ชันช่วย
def _get_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

# เพิ่มสินค้าเข้าตะกร้า
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)

    CartItem.objects.create(cart=cart, product=product, quantity=1)
    return redirect('shop:view_cart')



# แสดงตะกร้า
@login_required(login_url='shop:login')
def view_cart(request):
    cart = _get_cart(request.user)
    items = cart.items.select_related('product')
    total = sum(it.product.price * it.quantity for it in items)
    return render(request, 'cart.html', {'items': items, 'total': total})


# ลบสินค้า
def remove_from_cart(request):
    if request.method == 'POST':
        pid = request.POST.get('product_id')
        if request.user.is_authenticated:
            cart = _get_cart(request.user)
            CartItem.objects.filter(cart=cart, product_id=pid).delete()
        else:
            cart = request.session.get('cart', {})
            if pid in cart:
                del cart[pid]
                request.session['cart'] = cart
        messages.info(request, "นำสินค้าออกจากตะกร้าแล้ว")
    return redirect('shop:cart')

@require_POST
def update_cart(request):
    pid = request.POST.get('product_id')
    action = request.POST.get('action')

    if request.user.is_authenticated:
        cart = _get_cart(request.user)
        try:
            item = cart.items.get(product_id=pid)
            if action == "increase":
                item.quantity += 1
            elif action == "decrease" and item.quantity > 1:
                item.quantity -= 1
            item.save()
        except CartItem.DoesNotExist:
            pass
    return redirect('shop:cart')


@login_required(login_url='shop:login')
def my_orders(request):
    """แสดงรายการสั่งซื้อทั้งหมดของผู้ใช้"""
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product')
        .order_by('-created_at')
    )
    return render(request, 'my_orders.html', {'orders': orders})


@login_required(login_url='shop:login')
def my_order_detail(request, order_id):
    """แสดงรายละเอียดคำสั่งซื้อแต่ละรายการ"""
    try:
        order = (
            Order.objects.prefetch_related('items__product')
            .get(id=order_id, user=request.user)
        )
    except Order.DoesNotExist:
        messages.error(request, "ไม่พบคำสั่งซื้อนี้")
        return redirect('shop:my_orders')

    return render(request, 'my_order_detail.html', {'order': order})

# Checkout
@login_required(login_url='shop:login')
@transaction.atomic
def checkout(request):
    if request.method == 'POST':
        form = GuestCheckoutForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data['receiver_name']
            phone = form.cleaned_data['phone']
            address = form.cleaned_data['address_line']
            method = form.cleaned_data['payment_method']

            items = []
            total = 0
            cart = _get_cart(request.user)
            for it in cart.items.select_related('product'):
                items.append((it.product, it.quantity))
                total += it.quantity * it.product.price

            order = Order.objects.create(user=request.user, total_price=total)
            for p, q in items:
                OrderItem.objects.create(order=order, product=p, quantity=q, unit_price=p.price)
                p.stock = max(0, p.stock - q)
                p.save()

            Payment.objects.create(order=order, amount=total, method=method, status='pending')
            cart.items.all().delete()

            messages.success(request, "สั่งซื้อสำเร็จแล้ว!")
            return redirect('shop:order_success')
    else:
        form = GuestCheckoutForm()
    return render(request, 'checkout.html', {'form': form})

@login_required
def confirm_order(request):
    cart = Cart.objects.filter(user=request.user).first()
    checkout_info = request.session.get('checkout_info')

    if request.method == 'POST':
        # สร้างออเดอร์
        order = Order.objects.create(
            user=request.user,
            receiver_name=checkout_info['receiver_name'],
            phone=checkout_info['phone'],
            address_line=checkout_info['address_line'],
            payment_method=checkout_info['payment_method'],
        )

        for item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        # Payment
        Payment.objects.create(
            order=order,
            method=checkout_info['payment_method'],
            status='pending'
        )

        cart.delete()  # ล้างตะกร้า
        return redirect('shop:payment_success', order_id=order.id)

    return render(request, 'shop/confirm_order.html', {
        'cart': cart,
        'checkout_info': checkout_info,
    })



def order_success(request):
    return render(request, 'order_success.html')

@login_required(login_url='shop:login')
@transaction.atomic
def checkout(request):
    if request.method == 'POST':
        form = GuestCheckoutForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data['receiver_name']
            phone = form.cleaned_data['phone']
            address = form.cleaned_data['address_line']
            method = form.cleaned_data['payment_method']

            items = []
            total = 0
            cart = _get_cart(request.user)
            for it in cart.items.select_related('product'):
                items.append((it.product, it.quantity))
                total += it.quantity * it.product.price

            order = Order.objects.create(user=request.user, total_price=total)
            for p, q in items:
                OrderItem.objects.create(order=order, product=p, quantity=q, unit_price=p.price)
                p.stock = max(0, p.stock - q)
                p.save()

            Payment.objects.create(order=order, amount=total, method=method, status='pending')
            cart.items.all().delete()

            messages.success(request, "สั่งซื้อสำเร็จแล้ว!")
            return redirect('shop:order_success')
    else:
        form = GuestCheckoutForm()
    return render(request, 'checkout.html', {'form': form})