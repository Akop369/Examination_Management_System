from flask import Flask
from models import db, User, Class, Subject, Chapter, QuestionSet, Question

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # 1. Create all tables
    db.create_all()

    # 2. Complete academic hierarchy from 6th to 12th Streams
    all_classes = [
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

    created_classes = {}
    for c_name in all_classes:
        cls = Class.query.filter_by(class_name=c_name).first()
        if not cls:
            cls = Class(class_name=c_name)
            db.session.add(cls)
            db.session.commit()
        created_classes[c_name] = cls

    # 3. Default Teacher Account
    if not User.query.filter_by(email="teacher@test.com").first():
        teacher = User(
            full_name="Prof. Sharma",
            email="teacher@test.com",
            password="admin",
            role="teacher"
        )
        db.session.add(teacher)

    # 4. Default Student Account (Assigned to Class 10)
    class_10 = created_classes.get("Class 10")
    if not User.query.filter_by(email="rahul@test.com").first():
        student = User(
            full_name="Rahul Verma",
            email="rahul@test.com",
            password="123",
            role="student",
            roll_number="101",
            class_id=class_10.id
        )
        db.session.add(student)
    db.session.commit()

    # 5. Default Curriculum for testing
    math = Subject.query.filter_by(class_id=class_10.id, subject_name="Mathematics").first()
    if not math:
        math = Subject(class_id=class_10.id, subject_name="Mathematics")
        db.session.add(math)
        db.session.commit()

    chap = Chapter.query.filter_by(subject_id=math.id, chapter_no=1).first()
    if not chap:
        chap = Chapter(subject_id=math.id, chapter_no=1, title="Linear Equations")
        db.session.add(chap)
        db.session.commit()

    q_set = QuestionSet.query.filter_by(chapter_id=chap.id, set_title="Set A").first()
    if not q_set:
        q_set = QuestionSet(chapter_id=chap.id, set_title="Set A", time_limit=10, total_marks=10)
        db.session.add(q_set)
        db.session.commit()

        sample_questions = [
            Question(
                set_id=q_set.id,
                question_text=f"Question {i}: What is the value of x if x + {i} = {i * 2}?",
                option_a=str(i),
                option_b=str(i + 1),
                option_c=str(i + 2),
                option_d=str(i + 3),
                correct_option="A"
            )
            for i in range(1, 11)
        ]
        db.session.add_all(sample_questions)
        db.session.commit()

    print("Success: Database updated with Class 6 to 12th Arts!")