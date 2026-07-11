from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from extentions import db, login_manager
# import models 
from werkzeug.security import generate_password_hash, check_password_hash
from models import User

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
        return redirect(url_for("home"))
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
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)