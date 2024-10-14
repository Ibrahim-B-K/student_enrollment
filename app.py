from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from Crypto.Hash import SHA256  # Import SHA256 from pycryptodome
import smtplib  # Import smtplib for email
from email.mime.text import MIMEText  # For creating the email text body
import random
import string
import hashlib
from datetime import datetime




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
    
    cur = mysql.connection.cursor()
    
    # Fetch available departments to display in the dropdown
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()
    print(departments)  # Debug: Check if departments are fetched

    # Initialize courses and selected department
    courses = []
    department_id = None

    if request.method == 'POST':
        details = request.form
        first_name = details['first_name']
        last_name = details['last_name']
        dob = details['dob']
        email = details['email']
        phone = details['phone']
        address = details['address']
        exam_marks = details['exam_marks'].strip()  # Get marks as a string

        if not exam_marks:  # Check if exam marks are provided
            flash("Entrance exam marks are required.", "danger")
            return redirect(url_for('register'))

        try:
            exam_marks = int(exam_marks)  # Convert marks to integer
        except ValueError:
            flash("Invalid marks. Please enter a valid number.", "danger")
            return redirect(url_for('register'))

        department_id = details['department']
        course_id = details.get('course')  # Get selected course
        
        # Fetch the department's minimum marks requirement
        cur.execute("SELECT required_mark FROM departments WHERE department_id=%s", (department_id,))
        min_marks = cur.fetchone()
        
        if not min_marks:
            flash("Invalid department selected.", "danger")
            return redirect(url_for('register'))
        
        min_marks = min_marks[0]

        # Validate entrance exam marks against department's requirement
        if exam_marks < min_marks:
            flash("Your marks do not meet the department's requirements.", "danger")
            return redirect(url_for('register'))

        # Check if a course is selected
        if not course_id:
            flash("Please select a course.", "danger")
            return redirect(url_for('register'))

        # Check if the selected course has available seats
        cur.execute("SELECT capacity, (SELECT COUNT(*) FROM enrollments WHERE course_id=%s) AS enrolled_count FROM courses WHERE course_id=%s", (course_id, course_id))
        course_data = cur.fetchone()

        if course_data is None:
            flash("Selected course does not exist.", "danger")
            return redirect(url_for('register'))

        capacity = course_data[0]
        enrolled_count = course_data[1]

        if enrolled_count >= capacity:
            flash("The selected course is full. Please choose another course.", "danger")
            return redirect(url_for('register'))

        # Generate username and password
        username, password = generate_credentials()
        print(f"Generated Password: {password}")  # Debugging statement

        # Hash the password using MD5
        hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
        print(f"Hashed Password: {hashed_password}")  # Print the hashed password

        # Insert into the Students table with the generated credentials
        try:
            cur.execute(
                "INSERT INTO students(first_name, last_name, date_of_birth, email, phone_number, address, entrance_exam_marks, department_id, username, password) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (first_name, last_name, dob, email, phone, address, exam_marks, department_id, username, hashed_password)
            )
            mysql.connection.commit()

            # Get the current date
            current_date = datetime.now().strftime('%Y-%m-%d')

            # Insert into the Enrollments table
            cur.execute("INSERT INTO enrollments(student_id, course_id, enrollment_date) "
                        "VALUES ((SELECT student_id FROM students WHERE username=%s), %s, %s)",
                        (username, course_id, current_date))
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()  # Rollback on error
            print(f"Error during insertion: {e}")  # Print the error for debugging
            flash("An error occurred during registration: {}".format(str(e)), "danger")
            return redirect(url_for('register'))

        # Attempt to send email with credentials
        if send_email(email, username, password):
            flash("Registration successful! Your credentials have been sent to your email.", "success")
        else:
            flash("Registration successful, but failed to send email. Please contact support.", "warning")

        return redirect(url_for('login'))

    # Fetch courses based on selected department during GET request
    if request.method == 'GET':
        department_id = request.args.get('department')
        if department_id:
            cur.execute(
                "SELECT c.course_id, c.course_name FROM courses c "
                "JOIN course_department cd ON c.course_id = cd.course_id "
                "WHERE cd.department_id = %s", (department_id,)
            )
            courses = cur.fetchall()

    cur.close()

    return render_template('register.html', departments=departments, courses=courses, department_id=department_id)


@app.route('/get_courses', methods=['GET'])
def get_courses():
    department_id = request.args.get('department_id')
    
    cur = mysql.connection.cursor()
    cur.execute(
                "SELECT c.course_id, c.course_name FROM courses c "
                "JOIN course_department cd ON c.course_id = cd.course_id "
                "WHERE cd.department_id = %s", (department_id,)
            )
    courses = cur.fetchall()
    cur.close()

    # Convert the list of tuples to a list of dictionaries for JSON serialization
    course_list = [{'course_id': course[0], 'course_name': course[1]} for course in courses]
    
    return jsonify(course_list)





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
                # Fetch courses enrolled by the student along with instructor details
                cur.execute("""
                    SELECT c.course_name, i.username AS instructor_name, e.grade
                    FROM enrollments e
                    JOIN courses c ON e.course_id = c.course_id
                    JOIN instructors i ON c.instructor_id = i.instructor_id
                    WHERE e.student_id = %s
                """, (student[0],))  # Assuming student[0] is the student_id

                courses = cur.fetchall()

                return render_template('student_dashboard.html', student=student, courses=courses)
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
                # Fetch courses taught by the instructor and the students enrolled in those courses
                cur.execute("""
                    SELECT c.course_name, s.first_name, s.last_name, e.grade
                    FROM courses c
                    JOIN enrollments e ON c.course_id = e.course_id
                    JOIN students s ON e.student_id = s.student_id
                    WHERE c.instructor_id = %s
                """, (instructor[0],))  # Assuming instructor[0] is the instructor_id

                courses = cur.fetchall()

                return render_template('instructor_dashboard.html', instructor=instructor, courses=courses)
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






