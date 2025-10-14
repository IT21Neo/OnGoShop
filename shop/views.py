from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.conf import settings
from django.db.models import Q
from shop.forms import RegisterForm, AuthenticationForm, ProductForm, GuestCheckoutForm, OrderStatusForm, UserRoleForm, ProfileForm
from shop.models import User, Product, Category, Cart, CartItem, Order, OrderItem, Payment


# ตรวจสิทธิ์ admin
def admin_check(user):
    return user.is_authenticated and (getattr(user, 'role', '') in ['admin', 'owner'] or user.is_staff or user.is_superuser)

@login_required
def admin_dashboard(request):
    """
    แสดงหน้าแดชบอร์ดผู้ดูแลระบบ
    - สรุปข้อมูลสินค้า, สมาชิก, คำสั่งซื้อ, ยอดขาย
    - มีปุ่มลิงก์ไปหน้าจัดการ
    """
    # ตรวจสอบสิทธิ์เฉพาะ staff
    if not request.user.is_staff:
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        return redirect('shop:home')

    # --- ดึงข้อมูลสรุป ---
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(status='Paid').aggregate(Sum('total_price'))['total_price__sum'] or 0

    # --- ส่งข้อมูลไปหน้า HTML ---
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
    }

    return render(request, 'shop/admin_dashboard.html', context)

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

# หน้าโปรไฟล์ผู้ใช้
@login_required
def profile_view(request):
    """
    แสดงข้อมูลโปรไฟล์ของผู้ใช้ที่เข้าสู่ระบบ
    """
    return render(request, 'shop/profile.html', {
        'user': request.user
    })


# หน้าแก้ไขโปรไฟล์ผู้ใช้
@login_required
def profile_edit(request):
    """
    อนุญาตให้ผู้ใช้แก้ไขข้อมูลส่วนตัว (ชื่อ, อีเมล)
    """
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "อัปเดตโปรไฟล์เรียบร้อยแล้ว!")
            return redirect('shop:profile')
    else:
        form = ProfileForm(instance=user)

    return render(request, 'shop/profile_edit.html', {'form': form})


# แสดงสินค้าทั้งหมด (เพิ่มหมวดหมู่ + สินค้าแนะนำ)
def product_list(request):
    # ดึงสินค้าทั้งหมดจากฐานข้อมูล
    products = Product.objects.all()

    # --- ส่วนค้นหา ---
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # --- ส่วนเรียงลำดับ ---
    sort_option = request.GET.get('sort')
    if sort_option == 'price_low':
        products = products.order_by('price')
    elif sort_option == 'price_high':
        products = products.order_by('-price')
    elif sort_option == 'newest':
        products = products.order_by('-id')
    elif sort_option == 'oldest':
        products = products.order_by('id')

    # --- ดึงหมวดหมู่ทั้งหมด (ไว้แสดงใน sidebar หรือ dropdown) ---
    categories = Category.objects.all()

    # --- ดึงสินค้าสุ่มแนะนำ (5 ชิ้นล่าสุด) ---
    recommended = Product.objects.order_by('-id')[:5]

    # --- ส่วนเพิ่มสินค้าลงตะกร้า ---
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if not request.user.is_authenticated:
            messages.error(request, "กรุณาเข้าสู่ระบบก่อนเพิ่มสินค้าลงตะกร้า")
            return redirect('shop:login')

        product = get_object_or_404(Product, id=product_id)
        cart = _get_cart(request.user)

        # ถ้ามีสินค้านี้อยู่ในตะกร้าแล้ว ให้เพิ่มจำนวน
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, f"เพิ่ม {product.name} ลงในตะกร้าแล้ว!")
        return redirect('shop:product_list')

    return render(request, 'product_list.html', {
        'products': products,
        'categories': categories,
        'recommended': recommended,
    })

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
    """ดึงตะกร้าของผู้ใช้ ถ้ายังไม่มีให้สร้างใหม่"""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# เพิ่มสินค้าเข้าตะกร้า
@login_required(login_url='shop:login')
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))

        # ตรวจสอบว่าสินค้ามีอยู่จริงไหม
        product = Product.objects.filter(id=product_id).first()
        if not product:
            messages.error(request, "❌ ไม่พบสินค้าที่เลือก")
            return redirect("shop:product_list")

        # ดึงตะกร้าของผู้ใช้
        cart = _get_cart(request.user)

        # ตรวจว่ามีสินค้าเดิมในตะกร้ารึยัง
        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        # ถ้ามีอยู่แล้ว ให้เพิ่มจำนวน
        if not created:
            item.quantity += quantity
            item.save()

        messages.success(request, f"เพิ่ม {product.name} ลงในตะกร้าแล้ว!")
        return redirect("shop:product_list")

    return redirect("shop:product_list")


# แสดงหน้าตะกร้า
@login_required(login_url='shop:login')
def view_cart(request):
    cart = _get_cart(request.user)
    items = cart.items.select_related("product")

    # เพิ่ม subtotal ให้แต่ละ item
    for item in items:
        item.subtotal = item.product.price * item.quantity

    total = sum(item.subtotal for item in items)

    return render(request, "cart.html", {
        "items": items,
        "total": total
    })


# ลบสินค้าออกจากตะกร้า
@login_required(login_url='shop:login')
def remove_from_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        cart = _get_cart(request.user)

        # ลบสินค้าที่เลือกออกจากตะกร้า
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        messages.info(request, "นำสินค้าออกจากตะกร้าแล้ว")

    return redirect("shop:cart")


# ปรับจำนวนสินค้าในตะกร้า
@login_required(login_url='shop:login')
def update_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        action = request.POST.get("action")
        cart = _get_cart(request.user)

        item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        if item:
            if action == "increase":
                item.quantity += 1
            elif action == "decrease" and item.quantity > 1:
                item.quantity -= 1
            item.save()

    return redirect("shop:cart")


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
            # ✅ เก็บข้อมูลไว้ใน session ชั่วคราว
            request.session['checkout_info'] = {
                'receiver_name': form.cleaned_data['receiver_name'],
                'phone': form.cleaned_data['phone'],
                'address_line': form.cleaned_data['address_line'],
                'payment_method': form.cleaned_data['payment_method'],
            }
            return redirect('shop:confirm_order')
    else:
        form = GuestCheckoutForm()
    return render(request, 'checkout.html', {'form': form})

# ยืนยันคำสั่งซื้อ (หน้า Confirm Order)
@login_required
def confirm_order(request):
    """
    แสดงรายละเอียดคำสั่งซื้อก่อนยืนยันการชำระเงิน
    - ดึงคำสั่งซื้อที่ยังไม่ได้ชำระของผู้ใช้คนปัจจุบัน
    - แสดงรายการสินค้า + ราคารวม
    - เมื่อกดยืนยัน (POST) จะเปลี่ยนสถานะเป็น 'Paid' และไปหน้า success
    """
    try:
        # ดึงคำสั่งซื้อที่ยังไม่ได้ชำระของ user นี้
        order = Order.objects.filter(user=request.user, status='Pending').latest('id')
    except Order.DoesNotExist:
        messages.error(request, "ไม่พบคำสั่งซื้อที่รอการยืนยัน")
        return redirect('shop:cart')

    order_items = OrderItem.objects.filter(order=order)

    # ถ้าผู้ใช้กดยืนยันการชำระเงิน
    if request.method == 'POST':
        order.status = 'Paid'
        order.save()

        # สร้าง transaction record (optional)
        Payment.objects.create(
            order=order,
            amount=order.total_price,
            method='QR Code',
            transaction_id=f"TXN-{order.id}-{int(datetime.now().timestamp())}"
        )

        messages.success(request, "ชำระเงินเรียบร้อยแล้ว!")
        return redirect('shop:order_success')

    # ส่งข้อมูลไปหน้า confirm_order.html
    context = {
        'order': order,
        'order_items': order_items,
        'qr_code_path': '/static/images/qrcode.png',  # path ของรูป QR code
    }
    return render(request, 'shop/confirm_order.html', context)





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