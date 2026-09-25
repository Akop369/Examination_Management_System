from flask import Flask
from models import db, Class

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Full target list of classes and streams
    target_classes = [
        "Class 6",
        "Class 7",
        "Class 8",
        "Class 9",
        "Class 10",
        "11th Science",
        "11th Commerce",
        "11th Arts",
        "12th Science",
        "12th Commerce",
        "12th Arts"
    ]

    for c_name in target_classes:
        existing = Class.query.filter_by(class_name=c_name).first()
        if not existing:
            db.session.add(Class(class_name=c_name))
            print(f"Added: {c_name}")
        else:
            print(f"Already exists: {c_name}")

    db.session.commit()
    print("\nDatabase updated successfully with all classes and streams!")