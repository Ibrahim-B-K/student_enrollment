from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from Crypto.Hash import SHA256  # Import SHA256 from pycryptodome

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'student_enrollment'
mysql = MySQL(app)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        details = request.form
        first_name = details['first_name']
        last_name = details['last_name']
        dob = details['dob']
        email = details['email']
        phone = details['phone']
        address = details['address']
        exam_marks = details['exam_marks']
        department_id = details['department']
        username = details['username']
        password = details['password']  # Use plaintext password; SHA2 will be handled in SQL

        # Insert into the Students table with SHA2 for hashing
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Students(first_name, last_name, date_of_birth, email, phone_number, address, entrance_exam_marks, department_id, username, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, SHA2(%s, 256))",
            (first_name, last_name, dob, email, phone, address, exam_marks, department_id, username, password)
        )
        mysql.connection.commit()
        cur.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form['user_type']
        username = request.form['username']
        password = request.form['password']  # Use plaintext password

        cur = mysql.connection.cursor()
        if user_type == 'student':
            cur.execute("SELECT * FROM Students WHERE username=%s", (username,))
            user = cur.fetchone()
            password_index = 10  # Password is at index 10 in table Students
        else:
            cur.execute("SELECT * FROM Instructors WHERE username=%s", (username,))
            user = cur.fetchone()
            password_index = 7  # Password is at index 7 in table Instructors

        cur.close()

        # Compare the SHA2 hashed password
        if user and user[password_index] == SHA256.new(password.encode('utf-8')).hexdigest():
            session['logged_in'] = True
            session['username'] = username
            session['user_type'] = user_type
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.", "danger")
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        cur = mysql.connection.cursor()
        if session['user_type'] == 'student':
            # Fetch student details
            cur.execute("SELECT first_name, last_name FROM Students WHERE username=%s", (session['username'],))
            student = cur.fetchone()
            cur.close()
            if student:
                return render_template('student_dashboard.html', username=session['username'])
            else:
                flash("Student not found.", "danger")
                return redirect(url_for('login'))
        elif session['user_type'] == 'instructor':
            # Fetch instructor details
            cur.execute("SELECT first_name, last_name, instructor_id, phone_number, email FROM Instructors WHERE username=%s", (session['username'],))
            instructor = cur.fetchone()
            cur.close()
            if instructor:
                return render_template('instructor_dashboard.html', instructor=instructor)
            else:
                flash("Instructor not found.", "danger")
                return redirect(url_for('login'))
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


