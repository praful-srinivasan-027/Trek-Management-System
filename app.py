from flask import Flask
from extentions import db
# import models 
from models import User
from werkzeug.security import generate_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///trekking.db"
app.config["SECRET_KEY"]="dev"

db.init_app(app)
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
def home():
    return "Trekking Management System"

if __name__ == "__main__":
    app.run(debug=True)