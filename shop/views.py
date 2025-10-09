from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from shop.forms import RegisterForm, LoginForm, ProductForm, GuestCheckoutForm
from shop.models import Product, Cart, CartItem, Order, OrderItem, Payment


# ตรวจสิทธิ์ admin
def admin_check(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(admin_check, login_url='shop:login')
def admin_product_list(request):
    products = Product.objects.all().order_by('id')
    return render(request, 'admin_product_list.html', {'products': products})

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



# สมัครสมาชิก
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "สมัครสมาชิกสำเร็จแล้ว! โปรดเข้าสู่ระบบ")
            return redirect('shop:login')
        else:
            messages.error(request, "เกิดข้อผิดพลาดในการสมัครสมาชิก")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# เข้าสู่ระบบ
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"ยินดีต้อนรับ {username}!")
                return redirect('shop:product_list')
            else:
                messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = LoginForm()
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
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        product = Product.objects.get(id=product_id)

        if request.user.is_authenticated:
            cart = _get_cart(request.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            messages.success(request, f"เพิ่ม {product.name} ลงในตะกร้าแล้ว!")
        else:
            messages.error(request, "กรุณาเข้าสู่ระบบก่อนเพิ่มสินค้า")
            return redirect('shop:login')

    return redirect('shop:product_list')


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
    cart = _get_cart(request.user)
    items = cart.items.select_related('product')

    if not items.exists():
        messages.warning(request, "ตะกร้าของคุณว่างเปล่า")
        return redirect('shop:cart')

    total = sum(it.product.price * it.quantity for it in items)

    if request.method == 'POST':
        form = GuestCheckoutForm(request.POST)
        if form.is_valid():
            receiver = form.cleaned_data['receiver_name']
            phone = form.cleaned_data['phone']
            address = form.cleaned_data['address_line']
            method = form.cleaned_data['payment_method']

            # ✅ สร้าง Order
            order = Order.objects.create(user=request.user, total_price=total)

            # ✅ บันทึกรายการสินค้า
            for it in items:
                OrderItem.objects.create(
                    order=order,
                    product=it.product,
                    quantity=it.quantity,
                    unit_price=it.product.price
                )
                # ตัด stock
                it.product.stock = max(0, it.product.stock - it.quantity)
                it.product.save()

            # ✅ สร้าง Payment
            Payment.objects.create(
                order=order,
                amount=total,
                method=method,
                status='pending'
            )

            # ✅ เคลียร์ตะกร้า
            items.delete()

            messages.success(request, f"สั่งซื้อสำเร็จแล้ว! หมายเลขคำสั่งซื้อ #{order.id}")
            return redirect('shop:my_orders')
    else:
        form = GuestCheckoutForm()

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': items,
        'total_price': total
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