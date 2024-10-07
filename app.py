from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from Crypto.Hash import SHA256  # Import SHA256 from pycryptodome
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'student_enrollment'
mysql = MySQL(app)

# Function to generate random username and password
def generate_credentials():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return username, password

# Function to send email with generated credentials
def send_email(email, username, password):
    sender_email = "merlinhermes1327@gmail.com"  # Dummy account email
    sender_password = "merlinhermespassword@"       # Dummy account password
    subject = "Your Registration Details"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject

    body = f"Hello,\n\nYour registration has been successful. Here are your login credentials:\nUsername: {username}\nPassword: {password}\n\nPlease log in and change your password after logging in."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.example.com', 587)  # Update with your SMTP server
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

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

        # Generate username and password
        username, password = generate_credentials()

        # Hash the password using SHA256
        hashed_password = SHA256.new(password.encode('utf-8')).hexdigest()

        # Insert into the Students table with the generated credentials
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Students(first_name, last_name, date_of_birth, email, phone_number, address, entrance_exam_marks, department_id, username, password) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (first_name, last_name, dob, email, phone, address, exam_marks, department_id, username, hashed_password)
        )
        mysql.connection.commit()
        cur.close()

        # Send email with the username and password
        if send_email(email, username, password):
            flash("Registration successful! Your credentials have been emailed to you.", "success")
        else:
            flash("Registration successful! However, there was an issue sending the email.", "warning")

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

        # Compare the SHA256 hashed password
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


