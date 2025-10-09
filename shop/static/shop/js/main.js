document.addEventListener('click', async function(e){
  const t = e.target;
  if(t.matches('.btn-add') || t.matches('.btn-add *')){
    const btn = t.closest('.btn-add') || t;
    const id = btn.dataset.id;
    if(!id) return;
    const qty = btn.dataset.qty || 1;
    const resp = await fetch('/cart/add/', {
      method:'POST',
      headers:{'X-CSRFToken': window.CSRF_TOKEN, 'Content-Type':'application/x-www-form-urlencoded'},
      body: new URLSearchParams({product_id:id, quantity: qty})
    });
    const data = await resp.json();
    alert(data.message || 'เพิ่มลงตะกร้าแล้ว');
    if(data.cart_count !== undefined){
      document.getElementById('cart-count').textContent = data.cart_count;
    }
  }
});
