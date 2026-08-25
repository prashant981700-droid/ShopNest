
from flask import Flask, jsonify, request, send_from_directory, session
import sqlite3, hashlib, secrets, random, time, os
from pathlib import Path
from functools import wraps

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "database" / "shopnest.db"
FRONTEND = BASE / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
app.secret_key = os.getenv("SHOPNEST_SECRET", secrets.token_hex(32))

ADMIN_EMAIL = os.getenv("SHOPNEST_ADMIN_EMAIL", "admin@shopnest.com")
ADMIN_PASSWORD = os.getenv("SHOPNEST_ADMIN_PASSWORD", "admin123")

# Development OTP mode:
# The generated OTP is returned by /api/send-otp so the project can be
# demonstrated without an SMS provider. For real SMS OTP, connect Twilio/
# MSG91/2Factor/another provider in send_sms_otp().
otp_store = {}

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    DB.parent.mkdir(exist_ok=True)
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        category TEXT NOT NULL, price REAL NOT NULL, old_price REAL,
        rating REAL DEFAULT 4.0, image TEXT, description TEXT,
        stock INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        mobile TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        total REAL NOT NULL, status TEXT DEFAULT 'Placed',
        customer_name TEXT NOT NULL, phone TEXT NOT NULL,
        address TEXT NOT NULL, city TEXT NOT NULL, pincode TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL, quantity INTEGER NOT NULL,
        price REAL NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id))""")

    # Upgrade older project databases if these columns are missing.
    cols = {r["name"] for r in c.execute("PRAGMA table_info(products)").fetchall()}
    if "stock" not in cols: c.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
    if "created_at" not in cols: c.execute("ALTER TABLE products ADD COLUMN created_at TIMESTAMP")

    if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        data = [
        ("Floral Kurti","Women",499,899,4.5,"https://images.unsplash.com/photo-1583391733956-6c78276477e2?auto=format&fit=crop&w=700&q=80","Comfortable floral kurti for everyday wear.",25),
        ("Cotton Saree","Women",699,1199,4.4,"https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=700&q=80","Elegant lightweight saree.",20),
        ("Casual Shirt","Men",599,999,4.3,"https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=700&q=80","Regular-fit casual shirt.",30),
        ("Denim Jacket","Men",999,1599,4.6,"https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=700&q=80","Trendy denim jacket.",15),
        ("Running Sneakers","Footwear",799,1399,4.5,"https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80","Lightweight running sneakers.",18),
        ("College Backpack","Accessories",649,999,4.2,"https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=700&q=80","Spacious backpack for college.",22),
        ("Wireless Headphones","Electronics",1199,1999,4.4,"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=700&q=80","Comfortable wireless headphones.",12),
        ("Smart Watch","Electronics",1499,2499,4.3,"https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=700&q=80","Modern smartwatch.",10),
        ("Kitchen Storage Set","Home",549,899,4.1,"https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=700&q=80","Useful kitchen storage containers.",16),
        ("Table Lamp","Home",749,1199,4.5,"https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=700&q=80","Decorative lamp for study spaces.",14)]
        c.executemany("""INSERT INTO products
            (name,category,price,old_price,rating,image,description,stock)
            VALUES(?,?,?,?,?,?,?,?)""", data)
    c.commit()
    c.close()

def customer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "customer":
            return jsonify({"error":"Please login with mobile OTP first"}), 401
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error":"Admin login required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def send_sms_otp(mobile, otp):
    # Demo mode. Replace this function with a real SMS provider call.
    # Never hard-code production SMS credentials in source code.
    print(f"[SHOPNEST DEMO OTP] {mobile}: {otp}")
    return True

@app.route("/")
def home():
    return send_from_directory(FRONTEND, "index.html")

@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    mobile = (request.get_json() or {}).get("mobile","").strip()
    if not mobile.isdigit() or len(mobile) != 10:
        return jsonify({"error":"Enter a valid 10-digit Indian mobile number"}), 400
    otp = str(random.randint(100000, 999999))
    otp_store[mobile] = {"otp":otp, "expires":time.time()+300}
    send_sms_otp(mobile, otp)
    return jsonify({"success":True, "message":"OTP generated. Demo OTP is shown below.", "demo_otp":otp})

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    d=request.get_json() or {}
    mobile=d.get("mobile","").strip()
    otp=d.get("otp","").strip()
    record=otp_store.get(mobile)
    if not record or time.time() > record["expires"] or record["otp"] != otp:
        return jsonify({"error":"Invalid or expired OTP"}), 401
    c=db()
    u=c.execute("SELECT * FROM users WHERE mobile=?",(mobile,)).fetchone()
    if not u:
        name=d.get("name","ShopNest User").strip() or "ShopNest User"
        cur=c.execute("INSERT INTO users(name,mobile) VALUES(?,?)",(name,mobile))
        c.commit()
        u=c.execute("SELECT * FROM users WHERE id=?",(cur.lastrowid,)).fetchone()
    c.close()
    otp_store.pop(mobile,None)
    session.clear()
    session["role"]="customer"; session["user_id"]=u["id"]; session["user_name"]=u["name"]; session["mobile"]=mobile
    return jsonify({"success":True,"name":u["name"],"mobile":mobile})

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    d=request.get_json() or {}
    email=d.get("email","").strip().lower()
    password=d.get("password","")
    if email != ADMIN_EMAIL.lower() or password != ADMIN_PASSWORD:
        return jsonify({"error":"Invalid admin credentials"}), 401
    session.clear(); session["role"]="admin"; session["admin_email"]=ADMIN_EMAIL
    return jsonify({"success":True,"email":ADMIN_EMAIL})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success":True})

@app.route("/api/me")
def me():
    role=session.get("role")
    if role=="admin": return jsonify({"logged_in":True,"role":"admin","email":session["admin_email"]})
    if role=="customer": return jsonify({"logged_in":True,"role":"customer","name":session["user_name"],"mobile":session["mobile"]})
    return jsonify({"logged_in":False})

@app.route("/api/categories")
def categories():
    c=db(); rows=c.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall(); c.close()
    return jsonify(["All"]+[r["category"] for r in rows])

@app.route("/api/products")
def products():
    category=request.args.get("category","All"); search=request.args.get("search","").strip()
    q="SELECT * FROM products WHERE 1=1"; args=[]
    if category!="All": q+=" AND category=?"; args.append(category)
    if search: q+=" AND (name LIKE ? OR category LIKE ?)"; args += [f"%{search}%",f"%{search}%"]
    q+=" ORDER BY id DESC"
    c=db(); rows=c.execute(q,args).fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/products/<int:pid>")
def product(pid):
    c=db(); r=c.execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone(); c.close()
    return (jsonify(dict(r)),200) if r else (jsonify({"error":"Not found"}),404)

@app.route("/api/orders", methods=["POST"])
@customer_required
def create_order():
    d=request.get_json() or {}; items=d.get("items",[]); customer=d.get("customer",{})
    required=["name","phone","address","city","pincode","payment"]
    if not items or any(not customer.get(x) for x in required):
        return jsonify({"error":"Complete delivery details are required"}),400
    c=db(); total=0; valid=[]
    try:
        for item in items:
            p=c.execute("SELECT id,price,stock FROM products WHERE id=?",(item.get("id"),)).fetchone()
            qty=int(item.get("qty",0))
            if not p or qty<1: raise ValueError("Invalid cart item")
            if p["stock"] < qty: raise ValueError(f"Not enough stock for product #{p['id']}")
            total += p["price"]*qty; valid.append((p["id"],qty,p["price"]))
        cur=c.execute("""INSERT INTO orders(user_id,total,status,customer_name,phone,address,city,pincode,payment_method)
                         VALUES(?,?,?,?,?,?,?,?,?)""",
                      (session["user_id"],total,"Placed",customer["name"],customer["phone"],customer["address"],customer["city"],customer["pincode"],customer["payment"]))
        order_id=cur.lastrowid
        c.executemany("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",
                      [(order_id,pid,qty,price) for pid,qty,price in valid])
        for pid,qty,_ in valid: c.execute("UPDATE products SET stock=stock-? WHERE id=?",(qty,pid))
        c.commit()
        return jsonify({"success":True,"order_id":order_id,"message":"Order placed successfully","total":total})
    except ValueError as e:
        c.rollback(); return jsonify({"error":str(e)}),400
    finally: c.close()

@app.route("/api/orders")
@customer_required
def my_orders():
    c=db(); orders=c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
    result=[]
    for o in orders:
        items=c.execute("""SELECT oi.quantity,oi.price,p.name,p.image
                           FROM order_items oi JOIN products p ON p.id=oi.product_id
                           WHERE oi.order_id=?""",(o["id"],)).fetchall()
        x=dict(o); x["items"]=[dict(i) for i in items]; result.append(x)
    c.close(); return jsonify(result)

# ---------------- ADMIN ----------------

@app.route("/api/admin/stats")
@admin_required
def admin_stats():
    c=db()
    stats={
        "products":c.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "users":c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "orders":c.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "sales":c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status!='Cancelled'").fetchone()[0]
    }
    c.close(); return jsonify(stats)

@app.route("/api/admin/products")
@admin_required
def admin_products():
    c=db(); rows=c.execute("SELECT * FROM products ORDER BY id DESC").fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/admin/products", methods=["POST"])
@admin_required
def admin_add_product():
    d=request.get_json() or {}
    required=["name","category","price","stock","image","description"]
    if any(d.get(x) in (None,"") for x in required):
        return jsonify({"error":"Fill all product fields"}),400
    try:
        price=float(d["price"]); old=float(d.get("old_price") or price); stock=int(d["stock"]); rating=float(d.get("rating") or 4.0)
        if price<0 or stock<0: raise ValueError
    except ValueError: return jsonify({"error":"Price, stock and rating must be valid numbers"}),400
    c=db()
    cur=c.execute("""INSERT INTO products(name,category,price,old_price,rating,image,description,stock)
                     VALUES(?,?,?,?,?,?,?,?)""",(d["name"],d["category"],price,old,rating,d["image"],d["description"],stock))
    c.commit(); pid=cur.lastrowid; c.close()
    return jsonify({"success":True,"id":pid})

@app.route("/api/admin/products/<int:pid>", methods=["PUT"])
@admin_required
def admin_edit_product(pid):
    d=request.get_json() or {}
    c=db()
    exists=c.execute("SELECT id FROM products WHERE id=?",(pid,)).fetchone()
    if not exists: c.close(); return jsonify({"error":"Product not found"}),404
    try:
        price=float(d["price"]); old=float(d.get("old_price") or price); stock=int(d["stock"]); rating=float(d.get("rating") or 4.0)
    except (ValueError,TypeError,KeyError): c.close(); return jsonify({"error":"Invalid product data"}),400
    c.execute("""UPDATE products SET name=?,category=?,price=?,old_price=?,rating=?,image=?,description=?,stock=? WHERE id=?""",
              (d["name"],d["category"],price,old,rating,d["image"],d["description"],stock,pid))
    c.commit(); c.close(); return jsonify({"success":True})

@app.route("/api/admin/products/<int:pid>", methods=["DELETE"])
@admin_required
def admin_delete_product(pid):
    c=db()
    used=c.execute("SELECT COUNT(*) FROM order_items WHERE product_id=?",(pid,)).fetchone()[0]
    if used: c.close(); return jsonify({"error":"This product is linked to an order and cannot be deleted. Set stock to 0 instead."}),400
    c.execute("DELETE FROM products WHERE id=?",(pid,)); c.commit(); c.close()
    return jsonify({"success":True})

@app.route("/api/admin/orders")
@admin_required
def admin_orders():
    c=db()
    orders=c.execute("""SELECT o.*,u.mobile FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC""").fetchall()
    result=[]
    for o in orders:
        x=dict(o)
        x["items"]=[dict(i) for i in c.execute("""SELECT oi.quantity,oi.price,p.name
            FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=?""",(o["id"],)).fetchall()]
        result.append(x)
    c.close(); return jsonify(result)

@app.route("/api/admin/orders/<int:oid>/status", methods=["PUT"])
@admin_required
def admin_order_status(oid):
    status=(request.get_json() or {}).get("status")
    allowed=["Placed","Confirmed","Shipped","Delivered","Cancelled"]
    if status not in allowed: return jsonify({"error":"Invalid status"}),400
    c=db(); o=c.execute("SELECT status FROM orders WHERE id=?",(oid,)).fetchone()
    if not o: c.close(); return jsonify({"error":"Order not found"}),404
    c.execute("UPDATE orders SET status=? WHERE id=?",(status,oid)); c.commit(); c.close()
    return jsonify({"success":True})

if __name__=="__main__":
    init_db()
    app.run(debug=True)
