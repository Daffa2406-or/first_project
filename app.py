from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, session, url_for, jsonify

app = Flask(__name__)
app.secret_key = "boxing-secret"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",        
        database="boxing_fitnes"
    )

# ================= USER ROUTES =================
@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    user = None
    last_payment = None
    
    if "user_id" in session:
        cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
        user = cursor.fetchone()
        
        cursor.execute("SELECT * FROM payments WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (session["user_id"],))
        last_payment = cursor.fetchone()

    cursor.execute("SELECT * FROM packages")
    packages = cursor.fetchall()
    conn.close()

    return render_template("index.html", user=user, packages=packages, last_payment=last_payment)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            if user['role'] == 'admin':
                session['admin'] = True
            return redirect("/")
            
        return render_template("login.html", error="Email atau Password salah")
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, phone, password, package, level, role, status) VALUES (%s, %s, %s, %s, %s, 'Pemula', 'user', 'Active')",
                       (request.form["name"], request.form["email"], request.form["phone"], request.form["password"], request.form["package"]))
        user_id = cursor.lastrowid
        conn.commit()
        session["user_id"] = user_id
        session["name"] = request.form["name"]
        return redirect(f"/payment?package={request.form['package']}")
    except Exception as e:
        print("Error:", e)
        conn.rollback()
        return redirect("/")
    finally:
        conn.close()

@app.route("/upgrade")
def upgrade():
    if "user_id" not in session: return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM packages")
    packages = cursor.fetchall()
    conn.close()

    selected_name = request.args.get("package")
    selected_pkg = next((p for p in packages if p['name'] == selected_name), packages[0] if packages else None)
    
    return render_template("upgrade.html", user=user, packages=packages, selected_pkg=selected_pkg)

@app.route("/payment", methods=["GET"])
def payment_page():
    if "user_id" not in session: return redirect("/login")
    package_name = request.args.get("package")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT price FROM packages WHERE name=%s", (package_name,))
    pkg_data = cursor.fetchone()
    conn.close()
    
    if not pkg_data: return redirect("/upgrade")
    return render_template("payment.html", package=package_name, price=pkg_data['price'])

@app.route("/payment/process", methods=["POST"])
def payment_process():
    if "user_id" not in session: return redirect("/login")
    user_id = session["user_id"]
    package = request.form["package"]
    amount = request.form["amount"]
    file = request.files['proof_file']
    
    filename = ""
    if file:
        filename = secure_filename(file.filename)
        filename = f"{int(datetime.now().timestamp())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO payments (user_id, package_name, amount, proof_file, status) VALUES (%s, %s, %s, %s, 'Pending')",
                       (user_id, package, amount, filename))
        conn.commit()
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/contact", methods=["POST"])
def contact():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO messages (name, email, subject, message) VALUES (%s, %s, %s, %s)",
                       (request.form.get("name"), request.form.get("email"), request.form.get("subject"), request.form.get("message")))
        conn.commit()
    finally:
        conn.close()
    return redirect("/#contact")

# ================= ADMIN ROUTES =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"): return redirect("/login") 

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='user'")
    total_users = cursor.fetchone()['total']

    cursor.execute("SELECT SUM(amount) as total FROM payments WHERE status='Confirmed' AND DATE(created_at) = %s", (date.today(),))
    rev = cursor.fetchone()
    revenue_today = rev['total'] if rev['total'] else 0

    cursor.execute("SELECT COUNT(*) as total FROM payments WHERE status='Pending'")
    pending_orders = cursor.fetchone()['total']

    cursor.execute("SELECT package, COUNT(*) as count FROM users WHERE role='user' GROUP BY package ORDER BY count DESC LIMIT 5")
    package_stats = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role='user' ORDER BY id DESC LIMIT 5")
    recent_users = cursor.fetchall()

    cursor.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 5")
    messages = cursor.fetchall()

    conn.close()
    return render_template("admin/dashboard.html", total_users=total_users, revenue_today=revenue_today, 
                           pending_orders=pending_orders, package_stats=package_stats, recent_users=recent_users, 
                           messages=messages, page="dashboard")

@app.route("/admin/users")
def admin_users():
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role='user' ORDER BY id DESC")
    users = cursor.fetchall()
    conn.close()
    return render_template("admin/users.html", users=users, page="users")

@app.route("/admin/users/create", methods=["GET", "POST"])
def admin_create_user():
    if not session.get("admin"): return redirect("/login")
    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, phone, password, package, level, role, status) VALUES (%s, %s, %s, %s, %s, %s, 'user', 'Active')",
                       (request.form["name"], request.form["email"], request.form["phone"], request.form["password"], request.form["package"], request.form["level"]))
        conn.commit()
        conn.close()
        return redirect("/admin/users")
    return render_template("admin/user_form.html", action="Tambah")

@app.route("/admin/users/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_user(id):
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        cursor.execute("UPDATE users SET name=%s, email=%s, phone=%s, package=%s, level=%s WHERE id=%s",
                       (request.form["name"], request.form["email"], request.form["phone"], request.form["package"], request.form["level"], id))
        conn.commit()
        conn.close()
        return redirect("/admin/users")
    cursor.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cursor.fetchone()
    conn.close()
    return render_template("admin/user_form.html", action="Edit", user=user)

@app.route("/admin/users/delete/<int:id>")
def admin_delete_user(id):
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin/users")

@app.route("/admin/packages")
def admin_packages():
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM packages")
        packages = cursor.fetchall()
    except: packages = []
    conn.close()
    return render_template("admin/packages.html", packages=packages, page="packages")

@app.route("/admin/packages/edit/<int:id>", methods=["GET", "POST"])
def admin_edit_package(id):
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        cursor.execute("UPDATE packages SET name=%s, price=%s, duration=%s, description=%s WHERE id=%s",
                       (request.form["name"], request.form["price"], request.form["duration"], request.form["description"], id))
        conn.commit()
        conn.close()
        return redirect("/admin/packages")
    cursor.execute("SELECT * FROM packages WHERE id=%s", (id,))
    package = cursor.fetchone()
    conn.close()
    return render_template("admin/package_form.html", action="Edit", package=package)

@app.route("/admin/transactions")
def admin_transactions():
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT p.*, u.name as user_name FROM payments p LEFT JOIN users u ON p.user_id = u.id ORDER BY p.created_at DESC")
    transactions = cursor.fetchall()
    conn.close()
    return render_template("admin/transactions.html", transactions=transactions, page="transactions")

@app.route("/admin/transactions/confirm/<int:id>")
def confirm_payment(id):
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM payments WHERE id=%s", (id,))
        trx = cursor.fetchone()
        if trx:
            cursor.execute("UPDATE payments SET status='Confirmed' WHERE id=%s", (id,))
            cursor.execute("UPDATE users SET package=%s WHERE id=%s", (trx['package_name'], trx['user_id']))
            conn.commit()
    except Exception as e: conn.rollback()
    finally: conn.close()
    return redirect("/admin/transactions")

@app.route("/admin/transactions/reject/<int:id>")
def reject_payment(id):
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE payments SET status='Rejected' WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin/transactions")

@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not session.get("admin"): return redirect("/login")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        cursor.execute("UPDATE settings SET bank_name=%s, account_number=%s, account_holder=%s, whatsapp_number=%s WHERE id=1",
                       (request.form["bank_name"], request.form["account_number"], request.form["account_holder"], request.form["whatsapp_number"]))
        conn.commit()
    cursor.execute("SELECT * FROM settings WHERE id=1")
    settings_data = cursor.fetchone()
    conn.close()
    return render_template("admin/settings.html", settings=settings_data, page="settings")

@app.context_processor
def inject_site_settings():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM settings WHERE id=1")
        config = cursor.fetchone()
    except: config = None
    conn.close()
    if not config: config = {'bank_name': 'BCA', 'account_number': '000-000', 'account_holder': 'Admin', 'whatsapp_number': '6281'}
    return dict(site_config=config)


# Rest API Routes
def serialize_date(data):
    if isinstance(data, (date, datetime)):
        return data.isoformat()
    return data

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.form  
    
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    package = data.get('package')

    if not all([name, email, password, package]):
        return jsonify({'status': 'error', 'message': 'Data tidak lengkap'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Email sudah terdaftar'}), 409

        cursor.execute("""
            INSERT INTO users (name, email, phone, password, package, level, role, status)
            VALUES (%s, %s, %s, %s, %s, 'Pemula', 'user', 'Active')
        """, (name, email, phone, password, package))
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Registrasi berhasil',
            'user_id': cursor.lastrowid
        }), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or request.form
    
    email = data.get('email')
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        
        if user:
            user.pop('password', None)
            return jsonify({
                'status': 'success',
                'message': 'Login berhasil',
                'data': user
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Email atau password salah'}), 401
    finally:
        conn.close()

@app.route("/api/user/<int:user_id>", methods=["GET"])
def api_get_profile(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, email, phone, package, level, status, created_at FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        
        if user:
            user['created_at'] = serialize_date(user['created_at'])
            return jsonify({'status': 'success', 'data': user}), 200
        else:
            return jsonify({'status': 'error', 'message': 'User tidak ditemukan'}), 404
    finally:
        conn.close()

@app.route("/api/user/update", methods=["POST"])
def api_update_profile():
    data = request.form
    user_id = data.get('user_id')
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'User ID wajib diisi'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users SET name=%s, phone=%s, email=%s WHERE id=%s
        """, (name, phone, email, user_id))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Profil berhasil diupdate'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/api/packages", methods=["GET"])
def api_list_packages():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM packages")
        packages = cursor.fetchall()
        return jsonify({'status': 'success', 'data': packages}), 200
    finally:
        conn.close()

@app.route("/api/packages/<int:id>", methods=["GET"])
def api_detail_package(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM packages WHERE id=%s", (id,))
        pkg = cursor.fetchone()
        if pkg:
            return jsonify({'status': 'success', 'data': pkg}), 200
        return jsonify({'status': 'error', 'message': 'Paket tidak ditemukan'}), 404
    finally:
        conn.close()

@app.route("/api/payment", methods=["POST"])
def api_create_payment():
    user_id = request.form.get('user_id')
    package = request.form.get('package')
    amount = request.form.get('amount')
    file = request.files.get('proof_file')

    if not all([user_id, package, amount, file]):
        return jsonify({'status': 'error', 'message': 'Data pembayaran tidak lengkap'}), 400

    filename = secure_filename(file.filename)
    import time
    filename = f"{int(time.time())}_{filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO payments (user_id, package_name, amount, proof_file, status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (user_id, package, amount, filename))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Bukti pembayaran terkirim'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/api/payment/history/<int:user_id>", methods=["GET"])
def api_payment_history(user_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM payments WHERE user_id=%s ORDER BY created_at DESC
        """, (user_id,))
        payments = cursor.fetchall()
        
        for p in payments:
            p['created_at'] = serialize_date(p['created_at'])
            
        return jsonify({'status': 'success', 'data': payments}), 200
    finally:
        conn.close()

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM settings WHERE id=1")
        settings = cursor.fetchone()
        return jsonify({'status': 'success', 'data': settings}), 200
    finally:
        conn.close()

@app.route("/api/contact", methods=["POST"])
def api_send_message():
    data = request.get_json() or request.form
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        """, (name, email, subject, message))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Pesan terkirim'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/api/user/<int:id>", methods=["PUT"])
def api_update_user_put(id):
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'Tidak ada data dikirim'}), 400

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id=%s", (id,))
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'User tidak ditemukan'}), 404

        cursor.execute("""
            UPDATE users SET name=%s, email=%s, phone=%s WHERE id=%s
        """, (name, email, phone, id))
        conn.commit()
        
        return jsonify({'status': 'success', 'message': f'Data user ID {id} berhasil diupdate (PUT)'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/api/user/<int:id>/status", methods=["PATCH"])
def api_update_status_patch(id):
    data = request.get_json()
    status_baru = data.get('status') 

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET status=%s WHERE id=%s", (status_baru, id))
        conn.commit()
        return jsonify({'status': 'success', 'message': f'Status user ID {id} diubah jadi {status_baru} (PATCH)'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route("/api/user/<int:id>", methods=["DELETE"])
def api_delete_user_api(id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id=%s", (id,))
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'User tidak ditemukan'}), 404

        cursor.execute("DELETE FROM users WHERE id=%s", (id,))
        conn.commit()
        return jsonify({'status': 'success', 'message': f'User ID {id} berhasil dihapus permanen'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)