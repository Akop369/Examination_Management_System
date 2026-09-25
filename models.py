from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. Users Table (Students & Teachers)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    roll_number = db.Column(db.String(50), unique=True, nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)

# 2. Classes Table (Classes 6-10 and 11th/12th Streams)
class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), unique=True, nullable=False)
    subjects = db.relationship('Subject', backref='class_parent', lazy=True)
    students = db.relationship('User', backref='class_parent', lazy=True)

# 3. Subjects Table
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    chapters = db.relationship('Chapter', backref='subject_parent', lazy=True)

# 4. Chapters Table
class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    chapter_no = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    sets = db.relationship('QuestionSet', backref='chapter_parent', lazy=True)

# 5. Question Sets Table
class QuestionSet(db.Model):
    __tablename__ = 'question_sets'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    set_title = db.Column(db.String(50), nullable=False)  # e.g., "Set A"
    time_limit = db.Column(db.Integer, default=10, nullable=False)  # minutes
    total_marks = db.Column(db.Integer, default=10, nullable=False)
    questions = db.relationship('Question', backref='set_parent', lazy=True)

# 6. Questions Table (10 MCQs per set)
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'

# 7. Test Results Table
class TestResult(db.Model):
    __tablename__ = 'test_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # out of 10
    time_taken_seconds = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', backref='results', lazy=True)
    question_set = db.relationship('QuestionSet', backref='results', lazy=True)

# 8. Student Answers Table (Itemized Attempt Review)
class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('test_results.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option = db.Column(db.String(1), nullable=True)  # 'A', 'B', 'C', 'D', or None
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    test_result = db.relationship('TestResult', backref='detailed_answers', lazy=True)
    question = db.relationship('Question', backref='student_responses', lazy=True)