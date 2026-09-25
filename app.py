import io
import openpyxl
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from models import db, User, Class, Subject, Chapter, QuestionSet, Question, TestResult, StudentAnswer

app = Flask(__name__)
app.secret_key = 'super_secret_exam_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ----------------- AUTHENTICATION & REGISTRATION -----------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('teacher_dashboard' if session.get('role') == 'teacher' else 'select_exam'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['full_name'] = user.full_name
            session['role'] = user.role
            
            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            return redirect(url_for('select_exam'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        roll_number = request.form.get('roll_number')
        email = request.form.get('email')
        password = request.form.get('password')
        class_id = request.form.get('class_id', type=int)

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already exists. Check your details.', 'danger')
            return redirect(url_for('register'))

        new_student = User(
            full_name=full_name,
            email=email,
            password=password,
            role='student',
            roll_number=roll_number,
            class_id=class_id
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    classes = Class.query.order_by(Class.id).all()
    return render_template('register.html', classes=classes)

@app.route('/register-teacher', methods=['GET', 'POST'])
def register_teacher():
    SECRET_KEY_PHRASE = "TEACHER2026"  # Master authorization passcode

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        secret_code = request.form.get('secret_code')

        if secret_code != SECRET_KEY_PHRASE:
            flash("Invalid teacher authorization code. Access denied.", "danger")
            return redirect(url_for('register_teacher'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('register_teacher'))

        new_teacher = User(
            full_name=full_name,
            email=email,
            password=password,
            role='teacher',
            roll_number=None,
            class_id=None
        )
        db.session.add(new_teacher)
        db.session.commit()

        flash("Teacher account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register_teacher.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- STUDENT FLOW -----------------

@app.route('/select-exam')
def select_exam():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    student = User.query.get(session['user_id'])
    student_class = Class.query.get(student.class_id) if student.class_id else None
    subjects = Subject.query.filter_by(class_id=student.class_id).all() if student.class_id else []

    selected_subject_id = request.args.get('subject_id', type=int)
    selected_chapter_id = request.args.get('chapter_id', type=int)

    chapters = Chapter.query.filter_by(subject_id=selected_subject_id).all() if selected_subject_id else []
    sets = QuestionSet.query.filter_by(chapter_id=selected_chapter_id).all() if selected_chapter_id else []

    return render_template(
        'select_exam.html',
        student_class=student_class,
        subjects=subjects,
        chapters=chapters,
        sets=sets,
        selected_subject_id=selected_subject_id,
        selected_chapter_id=selected_chapter_id
    )

@app.route('/exam/<int:set_id>', methods=['GET', 'POST'])
def exam(set_id):
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    student = User.query.get(session['user_id'])
    q_set = QuestionSet.query.get_or_404(set_id)
    
    # Class-level boundary verification guard
    chapter = Chapter.query.get(q_set.chapter_id)
    subject = Subject.query.get(chapter.subject_id)
    if student.class_id and subject.class_id != student.class_id:
        flash("Unauthorized: You cannot access assessments outside your assigned class.", "danger")
        return redirect(url_for('select_exam'))

    questions = Question.query.filter_by(set_id=set_id).all()

    if request.method == 'POST':
        score = 0
        time_taken = request.form.get('time_taken', default=0, type=int)

        # 1. Create and commit the overall TestResult record
        result = TestResult(
            student_id=session['user_id'],
            set_id=q_set.id,
            score=0,
            time_taken_seconds=time_taken
        )
        db.session.add(result)
        db.session.commit()

        # 2. Track each question's selected answer and evaluate correctness
        answers_to_store = []
        for q in questions:
            user_choice = request.form.get(f'question_{q.id}')
            is_correct = (user_choice == q.correct_option) if user_choice else False
            
            if is_correct:
                score += 1

            answers_to_store.append(
                StudentAnswer(
                    result_id=result.id,
                    question_id=q.id,
                    selected_option=user_choice,
                    is_correct=is_correct
                )
            )

        # 3. Update the calculated score and commit detailed logs
        result.score = score
        db.session.add_all(answers_to_store)
        db.session.commit()
        
        return redirect(url_for('result', result_id=result.id))

    return render_template('exam.html', q_set=q_set, questions=questions)

@app.route('/result/<int:result_id>')
def result(result_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    res = TestResult.query.get_or_404(result_id)
    answers = StudentAnswer.query.filter_by(result_id=res.id).all()
    
    return render_template('result.html', result=res, answers=answers)

# ----------------- TEACHER ACTIONS & QUESTION BANK -----------------

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    classes = Class.query.order_by(Class.id).all()
    selected_class_id = request.args.get('class_id', type=int)
    students = User.query.filter_by(role='student', class_id=selected_class_id).all() if selected_class_id else []
    selected_student_id = request.args.get('student_id', type=int)
    
    query = TestResult.query
    if selected_student_id:
        query = query.filter_by(student_id=selected_student_id)
    elif selected_class_id:
        student_ids = [s.id for s in students]
        query = query.filter(TestResult.student_id.in_(student_ids))

    results = query.order_by(TestResult.submitted_at.desc()).all()

    return render_template(
        'teacher_dashboard.html',
        classes=classes,
        students=students,
        results=results,
        selected_class_id=selected_class_id,
        selected_student_id=selected_student_id
    )

@app.route('/teacher/manage-questions')
def manage_questions():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    classes = Class.query.order_by(Class.id).all()
    subjects = Subject.query.join(Class).order_by(Class.id, Subject.subject_name).all()
    chapters = Chapter.query.join(Subject).order_by(Subject.id, Chapter.chapter_no).all()

    return render_template('manage_questions.html', classes=classes, subjects=subjects, chapters=chapters)

@app.route('/teacher/add-subject', methods=['POST'])
def add_subject():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    class_id = request.form.get('class_id', type=int)
    subject_name = request.form.get('subject_name', '').strip()

    if class_id and subject_name:
        new_sub = Subject(class_id=class_id, subject_name=subject_name)
        db.session.add(new_sub)
        db.session.commit()
        flash(f"Subject '{subject_name}' added successfully!", "success")
    else:
        flash("Invalid subject details.", "danger")

    return redirect(url_for('manage_questions'))

@app.route('/teacher/add-chapter', methods=['POST'])
def add_chapter():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    subject_id = request.form.get('subject_id', type=int)
    chapter_no = request.form.get('chapter_no', type=int)
    title = request.form.get('title', '').strip()

    if subject_id and chapter_no and title:
        new_ch = Chapter(subject_id=subject_id, chapter_no=chapter_no, title=title)
        db.session.add(new_ch)
        db.session.commit()
        flash(f"Chapter '{title}' added successfully!", "success")
    else:
        flash("Invalid chapter details.", "danger")

    return redirect(url_for('manage_questions'))

@app.route('/teacher/add-question-set', methods=['POST'])
def add_question_set():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    chapter_id = request.form.get('chapter_id', type=int)
    set_title = request.form.get('set_title', '').strip()
    time_limit = request.form.get('time_limit', default=10, type=int)

    if not (chapter_id and set_title):
        flash("Please provide all set details.", "danger")
        return redirect(url_for('manage_questions'))

    q_set = QuestionSet(chapter_id=chapter_id, set_title=set_title, time_limit=time_limit, total_marks=10)
    db.session.add(q_set)
    db.session.commit()

    questions = []
    for i in range(1, 11):
        q_text = request.form.get(f'q_text_{i}')
        optA = request.form.get(f'q_optA_{i}')
        optB = request.form.get(f'q_optB_{i}')
        optC = request.form.get(f'q_optC_{i}')
        optD = request.form.get(f'q_optD_{i}')
        correct = request.form.get(f'q_correct_{i}')

        question = Question(
            set_id=q_set.id,
            question_text=q_text,
            option_a=optA,
            option_b=optB,
            option_c=optC,
            option_d=optD,
            correct_option=correct
        )
        questions.append(question)

    db.session.add_all(questions)
    db.session.commit()

    flash(f"Question Set '{set_title}' with 10 MCQs saved successfully!", "success")
    return redirect(url_for('manage_questions'))

@app.route('/teacher/export-excel')
def export_excel():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Exam Marks"

    headers = [
        "Roll No", "Student Name", "Class", "Subject", 
        "Chapter", "Set", "Score (/10)", "Time Taken (s)", "Submitted At"
    ]
    ws.append(headers)

    results = TestResult.query.all()
    for r in results:
        student = User.query.get(r.student_id)
        q_set = QuestionSet.query.get(r.set_id)
        chap = Chapter.query.get(q_set.chapter_id) if q_set else None
        sub = Subject.query.get(chap.subject_id) if chap else None
        cls = Class.query.get(sub.class_id) if sub else None

        ws.append([
            student.roll_number if student else "N/A",
            student.full_name if student else "Unknown",
            cls.class_name if cls else "N/A",
            sub.subject_name if sub else "N/A",
            chap.title if chap else "N/A",
            q_set.set_title if q_set else "N/A",
            r.score,
            r.time_taken_seconds,
            r.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="Student_Exam_Marks.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    app.run(debug=True)