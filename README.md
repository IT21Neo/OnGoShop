# 🛍️ OnGoShop

โปรเจกต์ **OnGoShop** เป็นเว็บแอปพลิเคชัน E-commerce พัฒนาโดยใช้ **Python (Django Framework)**  
โปรเจกต์นี้เป็นระบบฝั่งแอดมินสำหรับจัดการสินค้า หมวดหมู่ และคำสั่งซื้อภายในร้านค้าออนไลน์

---

## 🚀 วิธีติดตั้งและใช้งาน (Installation & Usage)

### 🔹 ขั้นตอนที่ 1: ติดตั้ง Python
ตรวจสอบให้แน่ใจว่ามี **Python 3.10 หรือใหม่กว่า** และ **pip** อยู่ในเครื่อง

```bash
python --version
pip --version
```

หากยังไม่มีให้ดาวน์โหลดจาก [https://www.python.org/downloads/](https://www.python.org/downloads/)

---

### 🔹 ขั้นตอนที่ 2: โคลนโปรเจกต์จาก GitHub
เปิด Terminal หรือ Command Prompt แล้วรันคำสั่ง:

```bash
git clone https://github.com/IT21Neo/OnGoShop.git
cd OnGoShop
```

---

### 🔹 ขั้นตอนที่ 3: สร้าง Virtual Environment
เพื่อแยกไลบรารีของโปรเจกต์ออกจากระบบหลัก

```bash
python -m venv venv
```

จากนั้นเปิดใช้งาน:

- **Windows**
  ```bash
  venv\Scripts\activate
  ```

- **macOS / Linux**
  ```bash
  source venv/bin/activate
  ```

---

### 🔹 ขั้นตอนที่ 4: ติดตั้ง Dependencies
หากไม่มี ให้ติดตั้ง Django ด้วยตนเองก่อน:

```bash
pip install django
```

---

### 🔹 ขั้นตอนที่ 5: สร้างฐานข้อมูล
รันคำสั่งเพื่อสร้างฐานข้อมูล (SQLite จะถูกสร้างอัตโนมัติ)

```bash
python manage.py migrate
```

---

### 🔹 ขั้นตอนที่ 6: สร้าง Superuser (สำหรับเข้าใช้งาน /admin)
```bash
python manage.py createsuperuser
```

จากนั้นตั้งชื่อผู้ใช้และรหัสผ่าน (ใช้สำหรับเข้าสู่ระบบแอดมิน)

---

### 🔹 ขั้นตอนที่ 7: รันเซิร์ฟเวอร์
เริ่มต้นเซิร์ฟเวอร์ด้วยคำสั่ง:

```bash
python manage.py runserver
```

เปิดเบราว์เซอร์ไปที่:
```
http://127.0.0.1:8000/
```

เข้าสู่ระบบแอดมินได้ที่:
```
http://127.0.0.1:8000/admin/
```

---

## ⚙️ ปัญหาที่อาจพบ

| ปัญหา | สาเหตุ | วิธีแก้ |
|--------|----------|----------|
| `ModuleNotFoundError: No module named 'django'` | ยังไม่ได้ติดตั้ง Django | `pip install django` |
| `Error: That port is already in use` | พอร์ต 8000 ถูกใช้แล้ว | `python manage.py runserver 8080` |
| Database Error | ยังไม่ได้ migrate | `python manage.py migrate` |

---

## 👨‍💻 ผู้พัฒนา (Developer)
**IT21Neo**

GitHub: [https://github.com/IT21Neo](https://github.com/IT21Neo)

---

> 💡 หมายเหตุ: โปรเจกต์นี้พัฒนาเพื่อการศึกษาและสาธิตการทำงานของ Django Framework
