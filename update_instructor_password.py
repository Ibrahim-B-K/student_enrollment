import mysql.connector
import bcrypt

# Connect to the MySQL database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',  # replace with your MySQL password
    database='student_enrollment'
)

cursor = db.cursor()

# Define the instructor's username and the new password
username = 'jk12'  # The username for the instructor
new_password = 'jk@123'  # The new password to set (the original password you want to hash)

# Hash the new password
hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

# Update the instructor's password in the database
cursor.execute("UPDATE Instructors SET password = %s WHERE username = %s", (hashed_password, username))
db.commit()

print(f"Password for instructor {username} updated successfully.")

# Close the connection
cursor.close()
db.close()
