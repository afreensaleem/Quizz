from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'quiz.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------------
# MODELS
# -------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    option1 = db.Column(db.String(200))
    option2 = db.Column(db.String(200))
    option3 = db.Column(db.String(200))
    option4 = db.Column(db.String(200))
    correct_answer = db.Column(db.String(200))
    difficulty = db.Column(db.String(50))


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    date = db.Column(db.String(100))


# -------------------------
# ROUTES
# -------------------------

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])


# -------------------------
# ONE QUESTION AT A TIME QUIZ
# -------------------------

@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect(url_for('login'))  # force login first
 
    # Get all questions in order
    questions = Question.query.order_by(Question.id).all()
    if not questions:
        return "No questions available in the quiz."

    # Initialize session for this quiz attempt
    session['question_ids'] = [q.id for q in questions]
    session['current'] = 0
    session['score'] = 0
    session['answers'] = []

    return redirect(url_for('question_page'))

@app.route("/question", methods=["GET", "POST"])
def question_page():
    if "user_id" not in session:
        return redirect(url_for('login'))  # force login first
        
    if 'question_ids' not in session:
        return redirect(url_for('dashboard'))  # force start from dashboard

    question_ids = session['question_ids']
    current_index = session.get('current', 0)

    # Quiz finished
    if current_index >= len(question_ids):
        return redirect(url_for('result'))

    question = Question.query.get(question_ids[current_index])

    if request.method == "POST":
        selected_option = request.form.get('option')
        session['answers'].append(selected_option)
        if selected_option == question.correct_answer:
            session['score'] += 1
        session['current'] = current_index + 1
        return redirect(url_for('question_page'))

    options = [question.option1, question.option2, question.option3, question.option4]
    progress = f"Question {current_index + 1} of {len(question_ids)}"

    return render_template("quiz.html", question=question, options=options, progress=progress)


@app.route("/result")
def result():
    score = session.get('score', 0)
    total = len(session.get('question_ids', []))

    # Optional: clear session quiz data
    session.pop('question_ids', None)
    session.pop('current', None)
    session.pop('score', None)
    session.pop('answers', None)

    return render_template("result.html", score=score, total=total)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
