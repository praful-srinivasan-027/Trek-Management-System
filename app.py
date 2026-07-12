from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from extentions import db, login_manager
# import models 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import User, Trek, TrekAssignment, Booking

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
    pending_staff = User.query.filter_by(
        role="staff",
        is_approved=False,
        is_blacklisted=False
    ).all()

    return render_template(
        "admin_dashboard.html",
        treks=treks,
        pending_staff=pending_staff
    )

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():
    if current_user.role != "staff":
        return "Access denied", 403

    assignments = TrekAssignment.query.filter_by(
        staff_id=current_user.id
    ).all()

    return render_template(
        "staff_dashboard.html",
        assignments=assignments
    )


@app.route("/user/dashboard")
@login_required
def user_dashboard():
    if current_user.role != "user":
        return "Access denied", 403

    location = request.args.get("location")
    difficulty = request.args.get("difficulty")

    query = Trek.query.filter_by(status="Open")

    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    open_treks = query.all()

    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "user_dashboard.html",
        open_treks=open_treks,
        bookings=bookings
    )

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

@app.route("/admin/trek/<int:trek_id>/assign", methods=["GET","POST"])
@login_required
def assign_staff(trek_id):
    if current_user.role!="admin":
        return "Access Denied", 403
    
    trek = db.get_or_404(Trek, trek_id)
    approved_staff = User.query.filter_by(
        role="staff",
        is_approved=True,
        is_blacklisted=False
    ).all()

    if request.method=="POST":
        staff_id = int(request.form.get("staff_id"))

        staff = db.session.get(User, staff_id)

        if (
            staff is None
            or staff.role != "staff"
            or not staff.is_approved
            or staff.is_blacklisted
        ):
            return "Invalid staff member", 400
        
        existing_assignment = TrekAssignment.query.filter_by(
            trek_id=trek.id,
            staff_id=staff.id
        ).first()

        if existing_assignment:
            return f"Staff is already assigned to this Trek", 400
        
        assignment = TrekAssignment(
            trek_id=trek_id,
            staff_id=staff_id
        )

        db.session.add(assignment)
        db.session.commit()

        return redirect(url_for("admin_dashboard"))
    return render_template("assign_staff.html", trek=trek, approved_staff=approved_staff)

@app.route("/admin/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
def approve_staff(staff_id):
    if current_user.role != "admin":
        return "Access denied", 403

    staff = db.get_or_404(User, staff_id)

    if staff.role != "staff":
        return "This user is not a staff member", 400

    staff.is_approved = True
    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/staff/treks/<int:trek_id>/update", methods=["GET", "POST"])
@login_required
def update_assigned_trek(trek_id):
    if current_user.role != "staff":
        return "Access denied", 403

    assignment = TrekAssignment.query.filter_by(
        trek_id=trek_id,
        staff_id=current_user.id
    ).first()

    if assignment is None:
        return "You are not assigned to this trek", 403

    trek = db.get_or_404(Trek, trek_id)

    if request.method == "POST":
        trek.available_slots = int(request.form.get("available_slots"))
        trek.status = request.form.get("status")

        db.session.commit()

        return redirect(url_for("staff_dashboard"))

    return render_template("update_assigned_trek.html", trek=trek)

@app.route("/user/treks/<int:trek_id>/book", methods=["POST"])
@login_required
def book_trek(trek_id):
    if current_user.role != "user":
        return "Access denied", 403

    trek = db.get_or_404(Trek, trek_id)

    if trek.status != "Open":
        return "This trek is not open for booking", 400

    if trek.available_slots <= 0:
        return "No slots available", 400

    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked"
    ).first()

    if existing_booking:
        return "You have already booked this trek", 400

    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked"
    )

    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    return redirect(url_for("user_dashboard"))

@app.route("/user/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    if current_user.role != "user":
        return "Access denied", 403

    booking = db.get_or_404(Booking, booking_id)

    # A user can cancel only their own booking
    if booking.user_id != current_user.id:
        return "Access denied", 403

    if booking.status != "Booked":
        return "This booking cannot be cancelled", 400

    booking.status = "Cancelled"
    booking.trek.available_slots += 1

    db.session.commit()

    return redirect(url_for("user_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)