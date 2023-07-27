from flask import Flask, render_template, request, redirect, url_for, json
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nishika'
app.config['MYSQL_DB'] = 'mcq_project'
mysql = MySQL(app)

# User Management
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.group = None

# (updated UserManager class)
class UserManager:
    def __init__(self):
        pass
        

    def register_user(self, username, password):
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            mysql.connection.commit()
            cur.close()

    def login_user(self, username, password):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user_data = cur.fetchone()
        cur.close()

        if user_data:
            user = User(user_data[1], user_data[2])
            return user
        else:
            return None


user_manager = UserManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username,password)
        user_manager.register_user(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = user_manager.login_user(username, password)
        if user:
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    logged_in_user = User("test_user", "password") 

    
    if logged_in_user:
        return render_template('dashboard.html', user=logged_in_user)
    else:
        return render_template('login.html', error="Invalid credentials")
    

# Exam Creation
class Question:
    def __init__(self, text, choices, correct_answer):
        self.text = text
        self.choices = choices
        self.correct_answer = correct_answer

class Exam:
    def __init__(self, id, name, duration, questions):
        self.id = id
        self.name = name
        self.duration = duration
        self.questions = questions

class ExamManager:
    def __init__(self):
        self.exams = {}

    def get_exam_by_name(self, name):
        for exam in self.exams.values():
            if exam.name == name:
                return exam
        return None

    def create_exam(self, id, name, duration, questions):
        exam = Exam(id, name, duration, questions)
        self.exams[name] = exam
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO exams (name, duration) VALUES (%s, %s)", (name, duration))
        mysql.connection.commit()

        exam_id = cur.lastrowid

        for question in questions:
            cur.execute("INSERT INTO questions (question_text) VALUES (%s)", (question.text,))
            question_id = cur.lastrowid

            for i, option in enumerate(question.choices, start=1):
                cur.execute("INSERT INTO options (question_id, option_text) VALUES (%s, %s)", (question_id, option))
                if i == question.correct_answer:
                    answer_text = chr(64 + i)  # Convert 1-based index to A, B, C, D, etc.
                    cur.execute("INSERT INTO answers (question_id, answer_text) VALUES (%s, %s)", (question_id, answer_text))

        mysql.connection.commit()
        cur.close()

exam_manager = ExamManager()

   

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if request.method == 'POST':
        name = request.form['name']
        duration = int(request.form['duration'])

        questions = []
        

        for i in range(1, 11): 
            question_text = request.form.get(f'question{i}')
            choices = [
                request.form.get(f'choice{i}_1'),
                request.form.get(f'choice{i}_2'),
                request.form.get(f'choice{i}_3'),
                request.form.get(f'choice{i}_4'),
            ]
            correct_answer = int(request.form.get(f'correct_answer{i}'))

            question = Question(question_text, choices, correct_answer)
            questions.append(question)

        exam_manager.create_exam(name, duration, questions)
        return redirect(url_for('dashboard'))

    return render_template('create_exam.html')


@app.route('/take_exam/<exam_name>', methods=['GET', 'POST'])
def take_exam(exam_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM exams WHERE name = %s", (exam_name,))
    exam_data = cur.fetchone()
    cur.close()
    exam_data = exam_manager.get_exam_by_name(exam_name)

    if not exam_data:
        return redirect(url_for('dashboard'))

    exam_id, exam_name, exam_duration = exam_data

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM questions WHERE exam_id = %s", (exam_id,))
    questions_data = cur.fetchall()
    cur.close()

    questions = []
    for question_data in questions_data:
        question_id, question_text = question_data

        cur = mysql.connection.cursor()
        cur.execute("SELECT option_text FROM options WHERE question_id = %s", (question_id,))
        choices_data = cur.fetchall()
        cur.close()

        choices = [choice_data[0] for choice_data in choices_data]

        cur = mysql.connection.cursor()
        cur.execute("SELECT answer_text FROM answers WHERE question_id = %s", (question_id,))
        correct_answer_data = cur.fetchone()
        cur.close()

        if correct_answer_data:
            correct_answer = correct_answer_data[0]
        else:
            correct_answer = None

        question = Question(question_text, choices, correct_answer)
        question.id = question_id
        questions.append(question)

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_answer = request.form.get(f'question_{question.id}', None)

            correct_answer_index = question.choices.index(question.correct_answer) + 1

            if selected_answer == question.correct_answer:
                score += 1

        return render_template('exam_result.html', exam_name=exam_name, score=score)

    
    return render_template('take_exam.html', exam_name=exam_name, duration=exam_duration, questions=questions)

@app.route('/join_group/<group_name>')
def join_group(group_name):
    group_id = 123 
    user_id = 456  
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_groups (user_id, group_id) VALUES (%s, %s)", (user_id, group_id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard'))

@app.route('/leave_group')
def leave_group():
    logged_in_user = User("test_user", "password")  

    if logged_in_user.group is None:
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET group_id = NULL WHERE id = %s", (logged_in_user.id,))
    mysql.connection.commit()
    cur.close()

    logged_in_user.group = None

    return redirect(url_for('dashboard'))

@app.route('/group_scores/<group_name>')
def display_group_scores(group_name):
    cur = mysql.connection.cursor()

    cur.execute("SELECT username, score FROM user_scores WHERE group_name = %s", (group_name,))
    group_scores = cur.fetchall()

    cur.close()

    return render_template('group_scores.html', group_name=group_name, group_scores=group_scores)

@app.route('/show_result/<exam_name>', methods=['GET', 'POST'])
def show_result(exam_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM exams WHERE name = %s", (exam_name,))
    exam_data = cur.fetchone()
    cur.close()

    if not exam_data:
        return redirect(url_for('dashboard'))

    exam_id, exam_name, exam_duration = exam_data
    user_id = 1

    cur = mysql.connection.cursor()
    cur.execute("SELECT answers, score FROM exam_submissions WHERE user_id = %s AND exam_id = %s", (user_id, exam_id))
    submission_data = cur.fetchone()
    cur.close()

    if not submission_data:
        return redirect(url_for('take_exam', exam_name=exam_name))

    user_answers, user_score = submission_data
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, correct_answer FROM questions WHERE exam_id = %s", (exam_id,))
    questions_data = cur.fetchall()
    cur.close()

    correct_answers_dict = {question_id: correct_answer for question_id, correct_answer in questions_data}


    score = 0
    user_answers_dict = json.loads(user_answers)
    for question_id, user_answer in user_answers_dict.items():
        if str(question_id) in correct_answers_dict and user_answer == correct_answers_dict[str(question_id)]:
            score += 1

    return render_template('exam_result.html', exam_name=exam_name, score=score, total_questions=len(correct_answers_dict))



if __name__ == '__main__':
    app.run(debug=True)