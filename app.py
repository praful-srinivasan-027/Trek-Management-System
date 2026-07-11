from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from extentions import db, login_manager
# import models 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import User, Trek

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///trekking.db"
app.config["SECRET_KEY"]="dev"

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view="login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role="admin").first()
    if admin is None:
        admin = User(
            name="Admin",
            email="admin@trek.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()

@app.route("/")
@login_required
def home():
    return f"Welcome {current_user.name}! Role: {current_user.role} "

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role=="admin":
        return redirect(url_for("admin_dashboard"))
    if current_user.role=="staff":
        return redirect(url_for("staff_dashboard"))
    return redirect(url_for("user_dashboard"))

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Access denied", 403

    treks = Trek.query.all()

    return render_template(
        "admin_dashboard.html",
        treks=treks
    )

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():
    if current_user.role != "staff":
        return "Access denied", 403

    return f"Staff Dashboard - Welcome {current_user.name}"


@app.route("/user/dashboard")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return "Access denied", 403

    return f"User Dashboard - Welcome {current_user.name}"

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        print(name, email, password, role)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already registered"
        if role not in ["user", "staff"]:
            return "invalid role"
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            is_approved=(role == "user")
        )

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user is None:
            return "Invalid Email Address"
        if not check_password_hash(user.password_hash,password):
            return "Invalid Password="
        if user.is_blacklisted:
            return "Your Account has been blocklisted"
        if user.role=="staff" and not user.is_approved:
            return "Your Staff Account is awaiting Admin Approval"
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user
    return redirect(url_for("login"))

@app.route("/admin/treks/create", methods=["GET", "POST"])
@login_required
def create_trek():
    if current_user.role != "admin":
        return "Access denied", 403

    if request.method == "POST":
        name = request.form.get("name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        duration = int(request.form.get("duration"))
        available_slots = int(request.form.get("available_slots"))
        status = request.form.get("status")
        start_date = datetime.strptime(
            request.form.get("start_date"), "%Y-%m-%d"
        ).date()
        end_date = datetime.strptime(
            request.form.get("end_date"), "%Y-%m-%d"
        ).date()

        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            available_slots=available_slots,
            status=status,
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(trek)
        db.session.commit()

        return redirect(url_for("admin_dashboard"))

    return render_template("create_trek.html")

@app.route("/admin/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@login_required
def edit_trek(trek_id):
    if current_user.role != "admin":
        return "Access denied", 403

    trek = db.get_or_404(Trek, trek_id)

    if request.method == "POST":
        trek.name = request.form.get("name")
        trek.location = request.form.get("location")
        trek.difficulty = request.form.get("difficulty")
        trek.duration = int(request.form.get("duration"))
        trek.available_slots = int(request.form.get("available_slots"))
        trek.status = request.form.get("status")
        trek.start_date = datetime.strptime(
            request.form.get("start_date"), "%Y-%m-%d"
        ).date()
        trek.end_date = datetime.strptime(
            request.form.get("end_date"), "%Y-%m-%d"
        ).date()

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_trek.html", trek=trek)

@app.route("/admin/treks/<int:trek_id>/delete", methods=["POST"])
@login_required
def delete_trek(trek_id):
    if current_user.role != "admin":
        return "Access denied", 403

    trek = db.get_or_404(Trek, trek_id)

    db.session.delete(trek)
    db.session.commit()

    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)