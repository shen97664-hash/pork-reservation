import sqlite3
import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "pork-shop-secret-key-2024"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pork.db")


# ── 数据库连接辅助 ──────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ── 管理员登录装饰器 ────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("请先登录管理员账号", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════
#  前台页面路由
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    db = get_db()
    featured = db.execute("SELECT * FROM pork_parts WHERE stock > 0 ORDER BY id LIMIT 4").fetchall()
    return render_template("index.html", featured=featured)


@app.route("/products")
def products():
    db = get_db()
    parts = db.execute("SELECT * FROM pork_parts ORDER BY id").fetchall()
    return render_template("products.html", parts=parts)


@app.route("/reserve/<int:part_id>", methods=["GET", "POST"])
def reserve(part_id):
    db = get_db()
    part = db.execute("SELECT * FROM pork_parts WHERE id = ?", (part_id,)).fetchone()
    if part is None:
        flash("该猪肉部位不存在", "danger")
        return redirect(url_for("products"))

    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        phone = request.form.get("phone", "").strip()
        quantity = request.form.get("quantity", "0").strip()
        appoint_date = request.form.get("appoint_date", "").strip()

        # 校验
        errors = []
        if not user_name:
            errors.append("请输入姓名")
        if not phone or not phone.isdigit() or len(phone) != 11:
            errors.append("请输入正确的11位手机号")
        try:
            quantity_int = int(quantity)
            if quantity_int <= 0:
                errors.append("数量必须大于0")
        except ValueError:
            errors.append("请输入有效的数量")
            quantity_int = 0
        if not appoint_date:
            errors.append("请选择预约日期")

        if quantity_int > part["stock"]:
            errors.append(f"库存不足！当前仅剩 {part['stock']} 斤")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("reserve.html", part=part)

        # 写入预约
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO reservations (user_name, phone, pork_part_id, quantity, appoint_date, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (user_name, phone, part_id, quantity_int, appoint_date, now),
        )
        # 扣减库存
        db.execute(
            "UPDATE pork_parts SET stock = stock - ? WHERE id = ?",
            (quantity_int, part_id),
        )
        db.commit()
        return redirect(url_for("reserve_success", name=user_name, qty=quantity_int, date=appoint_date))

    return render_template("reserve.html", part=part)


@app.route("/reserve/success")
def reserve_success():
    name = request.args.get("name", "")
    qty = request.args.get("qty", "")
    date = request.args.get("date", "")
    return render_template("success.html", name=name, qty=qty, date=date)


# ══════════════════════════════════════════════════════════════
#  管理员路由
# ══════════════════════════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM admin_users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("登录成功！", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("用户名或密码错误", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("已退出登录", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    total_reservations = db.execute("SELECT COUNT(*) as cnt FROM reservations").fetchone()["cnt"]
    today = datetime.now().strftime("%Y-%m-%d")
    today_reservations = db.execute(
        "SELECT COUNT(*) as cnt FROM reservations WHERE appoint_date = ?", (today,)
    ).fetchone()["cnt"]
    low_stock = db.execute("SELECT * FROM pork_parts WHERE stock < 10 ORDER BY stock").fetchall()
    recent = db.execute(
        "SELECT r.*, p.name as part_name FROM reservations r "
        "JOIN pork_parts p ON r.pork_part_id = p.id "
        "ORDER BY r.created_at DESC LIMIT 10"
    ).fetchall()
    return render_template(
        "admin_dashboard.html",
        total=total_reservations,
        today=today_reservations,
        low_stock=low_stock,
        recent=recent,
    )


@app.route("/admin/parts", methods=["GET", "POST"])
@admin_required
def admin_parts():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            part_id = request.form.get("part_id")
            price = request.form.get("price")
            stock = request.form.get("stock")
            description = request.form.get("description", "").strip()
            db.execute(
                "UPDATE pork_parts SET price=?, stock=?, description=? WHERE id=?",
                (float(price), int(stock), description, int(part_id)),
            )
            db.commit()
            flash("更新成功！", "success")
        elif action == "add":
            name = request.form.get("name", "").strip()
            price = request.form.get("price", "0")
            stock = request.form.get("stock", "0")
            description = request.form.get("description", "").strip()
            if name:
                db.execute(
                    "INSERT INTO pork_parts (name, description, price, stock) VALUES (?, ?, ?, ?)",
                    (name, description, float(price), int(stock)),
                )
                db.commit()
                flash(f"已添加：{name}", "success")
        elif action == "delete":
            part_id = request.form.get("part_id")
            db.execute("DELETE FROM pork_parts WHERE id=?", (int(part_id),))
            db.commit()
            flash("已删除", "info")

    parts = db.execute("SELECT * FROM pork_parts ORDER BY id").fetchall()
    return render_template("admin_parts.html", parts=parts)


@app.route("/admin/reservations")
@admin_required
def admin_reservations():
    db = get_db()
    status_filter = request.args.get("status", "")
    if status_filter:
        rows = db.execute(
            "SELECT r.*, p.name as part_name FROM reservations r "
            "JOIN pork_parts p ON r.pork_part_id = p.id "
            "WHERE r.status = ? ORDER BY r.created_at DESC",
            (status_filter,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT r.*, p.name as part_name FROM reservations r "
            "JOIN pork_parts p ON r.pork_part_id = p.id "
            "ORDER BY r.created_at DESC"
        ).fetchall()
    return render_template("admin_reservations.html", reservations=rows, current_status=status_filter)


@app.route("/admin/reservation/<int:res_id>/status", methods=["POST"])
@admin_required
def update_reservation_status(res_id):
    new_status = request.form.get("status")
    if new_status in ("pending", "confirmed", "cancelled"):
        db = get_db()
        old = db.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
        if old and new_status == "cancelled" and old["status"] != "cancelled":
            # 取消预约时退回库存
            db.execute(
                "UPDATE pork_parts SET stock = stock + ? WHERE id = ?",
                (old["quantity"], old["pork_part_id"]),
            )
        db.execute("UPDATE reservations SET status = ? WHERE id = ?", (new_status, res_id))
        db.commit()
        flash("状态已更新", "success")
    return redirect(url_for("admin_reservations"))


@app.route("/admin/change-password", methods=["GET", "POST"])
@admin_required
def admin_change_password():
    if request.method == "POST":
        old_pw = request.form.get("old_password", "")
        new_pw = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        db = get_db()
        user = db.execute("SELECT * FROM admin_users WHERE username = ?",
                          (session.get("admin_username"),)).fetchone()
        if not check_password_hash(user["password_hash"], old_pw):
            flash("原密码错误", "danger")
        elif len(new_pw) < 4:
            flash("新密码至少4位", "danger")
        elif new_pw != confirm:
            flash("两次输入的新密码不一致", "danger")
        else:
            db.execute("UPDATE admin_users SET password_hash=? WHERE id=?",
                       (generate_password_hash(new_pw), user["id"]))
            db.commit()
            flash("密码修改成功！", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("admin_change_password.html")


# ── 启动 ─────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
