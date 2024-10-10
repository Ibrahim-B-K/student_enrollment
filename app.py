from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from Crypto.Hash import SHA256  # Import SHA256 from pycryptodome
import smtplib  # Import smtplib for email
from email.mime.text import MIMEText  # For creating the email text body
import random
import string
import hashlib



app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'student_enrollment'
mysql = MySQL(app)

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# Function to generate random username and password
def generate_credentials():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return username, password

# Function to send email
def send_email(to_email, username, password):
    try:
        # Create the email content
        msg = MIMEText(f"Your username: {username}\nYour password: {password}")
        msg['Subject'] = 'Your Student Account Credentials'
        msg['From'] = 'sample.acc0122@gmail.com'
        msg['To'] = to_email

        # Connect to Gmail's SMTP server using SSL
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('sample.acc0122@gmail.com', 'jmra odmx wpcx qrgd')  # Login with app password

        # Send the email
        server.sendmail('sample.acc0122@gmail.com', to_email, msg.as_string())
        server.quit()

        return True  # Email sent successfully
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False  # Failed to send email

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
        print(f"Generated Password: {password}")  # Debugging statement

        # Hash the password using SHA256
        hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
        print(f"Hashed Password: {hashed_password}")  # Print the hashed password


        # Insert into the Students table with the generated credentials
        cur = mysql.connection.cursor()
        try:
            
            try:
                cur.execute(
                "INSERT INTO students(first_name, last_name, date_of_birth, email, phone_number, address, entrance_exam_marks, department_id, username, password) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (first_name, last_name, dob, email, phone, address, exam_marks, department_id, username, hashed_password)
                )
                mysql.connection.commit()
            except Exception as e:
                mysql.connection.rollback()  # Rollback on error
                print(f"Error during insertion: {e}")  # Print the error for debugging


            # Attempt to send email with credentials
            if send_email(email, username, password):
                flash("Registration successful! Your credentials have been sent to your email.", "success")
            else:
                flash("Registration successful, but failed to send email. Please contact support.", "warning")

            cur.execute("SELECT password FROM students WHERE username=%s", (username,))
            stored_hashed_password = cur.fetchone()[0]
            print(f"Stored Hashed Password: {stored_hashed_password}")  # Check what is stored

            # Additional debug to compare hashes
            if hashed_password == stored_hashed_password:
                print("Hashes match!")
            else:
                print("Hashes do not match!")

            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash("An error occurred during registration: {}".format(str(e)), "danger")
        finally:
            cur.close()

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form['user_type']  # Added to differentiate user types
        username = request.form['username']
        password = request.form['password']  # Use plaintext password

        cur = mysql.connection.cursor()
        try:
            if user_type == 'student':
                cur.execute("SELECT username, password FROM students WHERE username=%s", (username,))
                user = cur.fetchone()
                password_index = 10  # Password is at index 10 in table Students
            else:
                cur.execute("SELECT username, password FROM instructors WHERE username=%s", (username,))
                user = cur.fetchone()
                password_index = 7  # Password is at index 7 in table Instructors

            
            # Check the password based on user type
            if user_type == 'student' and user:
                # Hash the entered password using MD5
                entered_hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

            # Compare the MD5 hashed password
            if entered_hashed_password == user[1]:  # Assuming user[1] contains the hashed password
                session['logged_in'] = True
                session['username'] = username
                session['user_type'] = user_type
                return redirect(url_for('student_dashboard'))
            elif user_type == 'instructor' and user and user[1] == SHA256.new(password.encode('utf-8')).hexdigest():
                session['logged_in'] = True
                session['username'] = username
                session['user_type'] = user_type
                return redirect(url_for('instructor_dashboard'))

                '''# Redirect based on user type
                if user_type == 'student':
                    return redirect(url_for('student_dashboard'))  # Redirect to student dashboard
                elif user_type == 'instructor':
                    return redirect(url_for('instructor_dashboard'))  # Redirect to instructor dashboard'''
            else:
                flash("Invalid credentials, please try again.", "danger")
        finally:
            cur.close()

    return render_template('login.html')

# Student Dashboard route
@app.route('/student_dashboard')
def student_dashboard():
    if 'logged_in' in session and session['user_type'] == 'student':
        username = session['username']

        # Fetch student details
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM students WHERE username=%s", (username,))
            student = cur.fetchone()
            if student:
                return render_template('student_dashboard.html', student=student)
            else:
                flash("Student not found.", "warning")
                return redirect(url_for('login'))
        finally:
            cur.close()
    else:
        flash("Please log in as a student first.", "warning")
        return redirect(url_for('login'))

# Instructor Dashboard route
@app.route('/instructor_dashboard')
def instructor_dashboard():
    if 'logged_in' in session and session['user_type'] == 'instructor':
        username = session['username']

        # Fetch instructor details
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM Instructors WHERE username=%s", (username,))
            instructor = cur.fetchone()
            if instructor:
                return render_template('instructor_dashboard.html', instructor=instructor)
            else:
                flash("Instructor not found.", "warning")
                return redirect(url_for('login'))
        finally:
            cur.close()
    else:
        flash("Please log in as an instructor first.", "warning")
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)






