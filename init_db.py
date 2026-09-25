from flask import Flask
from models import db, User, Class, Subject, Chapter, QuestionSet, Question

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # 1. Create all 7 tables
    db.create_all()

    # 2. Add sample Class, Subject, Chapter, and Question Set
    if not Class.query.first():
        cls = Class(class_name="Class 10")
        db.session.add(cls)
        db.session.commit()

        # Users: Teacher & Student
        teacher = User(
            full_name="Prof. Sharma", 
            email="teacher@test.com", 
            password="admin", 
            role="teacher"
        )
        student = User(
            full_name="Rahul Verma", 
            email="rahul@test.com", 
            password="123", 
            role="student", 
            roll_number="101", 
            class_id=cls.id
        )
        db.session.add_all([teacher, student])

        # Subject & Chapter
        math = Subject(class_id=cls.id, subject_name="Mathematics")
        db.session.add(math)
        db.session.commit()

        chap = Chapter(subject_id=math.id, chapter_no=1, title="Linear Equations")
        db.session.add(chap)
        db.session.commit()

        q_set = QuestionSet(chapter_id=chap.id, set_title="Set A", time_limit=10, total_marks=10)
        db.session.add(q_set)
        db.session.commit()

        # Insert exactly 10 MCQs
        sample_questions = [
            Question(set_id=q_set.id, question_text=f"Question {i}: What is the value of x if x + {i} = {i*2}?", 
                     option_a=str(i), option_b=str(i+1), option_c=str(i+2), option_d=str(i+3), 
                     correct_option="A") 
            for i in range(1, 11)
        ]
        db.session.add_all(sample_questions)
        db.session.commit()
        print("Database initialized and loaded with 10 questions successfully!")
    else:
        print("Database already contains data.")