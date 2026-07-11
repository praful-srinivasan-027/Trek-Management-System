from extentions import db
from datetime import datetime, timezone

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)

    bookings = db.relationship(
        "Booking",
        back_populates="user"
    )
    staff_assignments = db.relationship(
        "TrekAssignment",
        back_populates="staff"
    )
class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    bookings = db.relationship(
        "Booking",
        back_populates="trek"
    )
    staff_assignments = db.relationship(
        "TrekAssignment",
        back_populates="trek"
    )

class TrekAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(
        db.Integer,
        db.ForeignKey("trek.id"),
        nullable=False
    )
    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
    #TODO: Check this part later once
    __table_args__ = (
        db.UniqueConstraint(
            "trek_id",
            "staff_id",
            name="unique_trek_staff_assignment"
        ),
    )

    staff = db.relationship(
        "User",
        back_populates="staff_assignments"
    )
    trek = db.relationship(
        "Trek",
        back_populates="staff_assignments"
    )

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
    trek_id = db.Column(
        db.Integer,
        db.ForeignKey("trek.id"),
        nullable=False
    )
    booking_date = db.Column(
        db.DateTime,
        nullable=False,
        default= lambda: datetime.now(timezone.utc)
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="Booked"
    )

    user = db.relationship(
        "User",
        back_populates="bookings"
    )
    trek = db.relationship(
        "Trek",
        back_populates="bookings"
    )