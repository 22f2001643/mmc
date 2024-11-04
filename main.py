from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session,send_file
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import smtplib
import csv
from io import BytesIO,StringIO
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
from flask_mail import Mail, Message

app = Flask(__name__, template_folder="marvellousmedicalcenter-main")
app.secret_key = "TH!(EN)!ND@)AL)!"
app.config['UPLOAD_FOLDER'] = 'uploads'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'thendralraj19@gmail.com'
app.config['MAIL_PASSWORD'] = '##tr@619'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Database setup (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'mmc.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
mail = Mail(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Model for storing check-ups and appointments
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)  # Add email field
    booking_type = db.Column(db.String(50), nullable=False)
    appointment_date = db.Column(db.String(100), nullable=False)
    appointment_time = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)

class Booking_appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)  # Add email field
    booking_type = db.Column(db.String(50), nullable=False)
    appointment_date = db.Column(db.String(100), nullable=False)
    appointment_time = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(20), nullable=False, default='pending')

    def __repr__(self):
        return f'<Booking {self.first_name} {self.last_name}>'

# Initialize the database (create tables)
with app.app_context():
    db.create_all()

# Route to render the form page
@app.route('/', methods=['GET', 'POST'])
def index():
    bookings = Booking_appointment.query.all()  # Fetch all bookings to display in the template
    return render_template('index.html', bookings=bookings)


@app.route('/dental')
def dental():
    return render_template('dental.html')

@app.route('/orthodontics')
def ortho():
    return render_template('ortho.html')

@app.route('/general')
def general():
    return render_template('general.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dental_page')
def dental_page():
    return render_template('book_dental.html')

@app.route('/admin')
def admin():
    # Retrieve the user from the session
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    # Get the current user
    user = User.query.get(user_id)

    # Ensure the user is an admin (you may want to improve the admin check with a proper role field)
    if user.first_name == "Marvellous" and user.last_name == "Hospital":
        # Retrieve all users and all booking appointments
        all_users = User.query.all()  # Fetch all users
        bookings = Booking_appointment.query.all()  # Fetch all bookings

        # Render the admin dashboard template with all the users and bookings
        return render_template('login.html', user=user, all_users=all_users, bookings=bookings)
    else:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))




@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    
    print(f"User ID from session: {user_id}")  # Debug print

    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user = User.query.get(user_id)
    print(f"User fetched from DB: {user}")  # Debug print

    if not user:
        return redirect(url_for('login'))  # Redirect if user not found

    # Fetch the bookings for the logged-in user
    bookings = Booking_appointment.query.filter_by(user_id=user.id).all()

    return render_template('dashboard.html', user=user, bookings=bookings)




@app.route('/signup', methods=['GET','POST'])
def signup():
    # Get the form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = request.form.get('password')

    # Check if the email already exists
    if User.query.filter_by(email=email).first():
        flash("Email already exists. Please use a different one.", "error")
        return jsonify({'status': 'error', 'message': 'Email already exists'})

    # Ensure all fields are filled
    if not all([first_name, last_name, address, phone, email, password]):
        flash("All fields are required!", "error")
        return jsonify({'status': 'error', 'message': 'All fields are required'})

    # Create a new user instance
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        address=address,
        phone=phone,
        email=email,
        password=generate_password_hash(password)
    )

    try:
        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        flash(f"Account created successfully for {first_name} {last_name}.", "success")
        return redirect(url_for('index'))

    except Exception as e:
        # Handle any errors, such as database issues
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred while registering the user', 'error': str(e)})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle the login form submission
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password')

        print(f"Attempting to log in user: {first_name} {last_name} with phone: {phone}")  # Debug print

        # Query the User table to find the matching user
        user = User.query.filter_by(first_name=first_name, last_name=last_name, phone=phone).first()

        print(f"User found: {user}")  # Debug print

        if not user:
            flash('User not found or Invalid Password', 'danger')
            return redirect(url_for('login'))

        # Store the user ID in session
        session['user_id'] = user.id
        print(f"User ID stored in session: {session['user_id']}")  # Debug print

        # Check if the user is the admin (e.g., specific credentials)
        if (first_name == "Marvellous" and last_name == "Hospital" and 
            phone == "065614266" and password == "123456"):
            return redirect(url_for('admin'))  # Redirect to admin page

        # Otherwise, redirect to normal user dashboard
        return redirect(url_for('dashboard'))

    # Render the login page for GET request
    return render_template('login.html')





# Route to handle form submission for Check-up
@app.route('/book_checkup', methods=['GET', 'POST'])
def book_checkup():
    # Retrieve form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    email = request.form.get('email')
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    specialty = request.form.get('specialty')

    # Ensure all fields are filled in
    if not all([first_name, last_name, address, phone, email, appointment_date, appointment_time, specialty]):
        flash("All fields are required!", "error")
        return redirect(url_for('index'))

    # Check if the selected date and time slot already has two appointments
    appointment_count = Booking_appointment.query.filter_by(
        appointment_date=appointment_date,
        appointment_time=appointment_time
    ).count()

    if appointment_count >= 2:
        flash(f"Time slot on {appointment_date} at {appointment_time} is fully booked.", "error")
        return redirect(url_for('index'))

    # Retrieve user_id based on email or phone number
    user = User.query.filter((User.email == email) | (User.phone == phone)).first()
    
    if user is None:
        flash("User not found. Please register first.", "error")
        return redirect(url_for('index'))

    # Create a new booking instance
    new_booking = Booking_appointment(
        first_name=first_name,
        last_name=last_name,
        address=address,
        phone=phone,
        email=email,
        booking_type="checkup",
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        specialty=specialty,
        user_id=user.id  # Set user_id from the found user
    )

    # Save the new booking to the database
    db.session.add(new_booking)
    db.session.commit()

    # Display success message and redirect
    flash(f"Appointment booked successfully for {first_name} {last_name} on {appointment_date} at {appointment_time}.", "success")
    return redirect(url_for('dashboard'))

# Route to handle form submission for Appointment
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    # Retrieve form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    email = request.form.get('email')
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    specialty = request.form.get('specialty')
    booking_type = request.form.get('booking_type')

    # Ensure all fields are filled in
    if not all([first_name, last_name, address, phone, email, appointment_date, appointment_time, specialty,booking_type]):
        flash("All fields are required!", "error")
        return redirect(url_for('index'))

    # Check if the selected date and time slot already has two appointments
    appointment_count = Booking_appointment.query.filter_by(
        appointment_date=appointment_date,
        appointment_time=appointment_time
    ).count()

    if appointment_count >= 2:
        flash(f"Time slot on {appointment_date} at {appointment_time} is fully booked.", "error")
        return redirect(url_for('index'))

    # Retrieve user_id based on email or phone number
    user = User.query.filter((User.email == email) | (User.phone == phone)).first()
    
    if user is None:
        flash("User not found. Please register first.", "error")
        return redirect(url_for('index'))

    # Create a new booking instance
    new_booking = Booking_appointment(
        first_name=first_name,
        last_name=last_name,
        address=address,
        phone=phone,
        email=email,
        booking_type=booking_type,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        specialty=specialty,
        user_id=user.id  # Set user_id from the found user
    )

    # Save the new booking to the database
    db.session.add(new_booking)
    db.session.commit()

    # Display success message and redirect
    flash(f"Appointment booked successfully for {first_name} {last_name} on {appointment_date} at {appointment_time}.", "success")
    return redirect(url_for('dashboard'))




# Route to get available times for the selected date
@app.route('/get_available_times', methods=['POST'])
def get_available_times():
    selected_date = request.json.get('date')
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

    # Fetch existing appointments for the selected date
    existing_appointments = Appointment.query.filter_by(date=selected_date).all()
    
    # Extract existing times
    booked_times = {appointment.time for appointment in existing_appointments}

    # Define your full list of available time slots
    all_time_slots = [
        '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM',
        '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM', 
        '5:00 PM', '6:00 PM', '7:00 PM', '8:00 PM', 
        '9:00 PM'
    ]
    
    # Filter out booked times
    available_times = [time for time in all_time_slots if time not in booked_times]

    return jsonify(available_times)

# Route to cancel an appointment
@app.route('/cancel_appointment/<int:booking_id>', methods=['POST'])
def cancel_appointment(booking_id):
    booking = Booking_appointment.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash("Appointment canceled successfully.", "success")
    return redirect(url_for('index'))



@app.route('/send_email', methods=['POST'])
def send_email():
    email_recipient = request.form['email_recipient']
    pdf_file = request.files['pdf_file']
    
    if pdf_file:
        filename = secure_filename(pdf_file.filename)
        pdf_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Normally, send email with the PDF attached
        # For demonstration purposes, the code to send email is simplified:
        flash(f"PDF sent to {email_recipient}.", "success")
    
    return redirect(url_for('index'))

@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    booking = Booking_appointment.query.get(booking_id)

    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash("Booking deleted successfully.", "success")
    else:
        flash("Booking not found.", "error")

    return redirect(url_for('dashboard'))

@app.route('/update_booking_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    new_action = request.form.get('action')  # Get 'action' from the form

    if not new_action:
        flash("No action provided.", "error")
        return redirect(url_for('admin'))
    booking = Booking_appointment.query.get(booking_id)

    if booking:
        booking.action = new_action
        try:
            db.session.commit() 
            flash(f"Booking status updated to {new_action}.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating booking status.", "error")
            print(f"Error: {e}")
    else:
        flash("Booking not found.", "error")
    
    return redirect(url_for('admin'))


@app.route('/contactmail', methods=['GET', 'POST'])
def contactmail():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Send email to the company
        msg = Message(subject=f"New Contact Us Message from {name}",
                      sender=email,
                      recipients=['thendralraj19@gmail.com'],
                      body=f"Name: {name}\nEmail: {email}\nMessage: {message}")
        try:
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred while sending your message: {str(e)}', 'danger')

    return render_template('contact.html')

@app.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('user_id', None)  # Remove user ID from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))  # Redirect to index or login page

@app.route('/export_users', methods=['GET'])
def export_csv():
    # Fetch all user data from the User model
    users = User.query.all()
    
    # Create a CSV in memory using StringIO
    output = StringIO()
    
    # Write CSV header
    output.write('First Name,Last Name,Address,Phone,Email\n')
    
    # Write CSV rows
    for user in users:
        # Escape commas and any special characters properly for CSV format
        row = f'"{user.first_name}","{user.last_name}","{user.address}","{user.phone}","{user.email}"\n'
        output.write(row)
    
    output.seek(0)  # Reset the stream position to the beginning
    
    # Convert StringIO to BytesIO for Flask's send_file
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    # Return the CSV as a file attachment with the correct MIME type
    return send_file(mem, mimetype='text/csv', download_name='users.csv', as_attachment=True)

@app.route('/export_appointments_csv', methods=['GET'])
def export_appointments_csv():
    # Fetch all booking appointment data from the Booking_appointment model
    appointments = Booking_appointment.query.all()
    
    # Create a CSV in memory using StringIO (Excel expects a plain text-based CSV format)
    output = StringIO()
    
    # Write CSV header
    output.write('First Name,Last Name,Address,Phone,Email,Booking Type,Appointment Date,Appointment Time,Specialty,Action\n')
    
    # Write CSV rows
    for appointment in appointments:
        # Escape commas and any special characters properly for CSV format
        row = f'"{appointment.first_name}","{appointment.last_name}","{appointment.address}","{appointment.phone}","{appointment.email}","{appointment.booking_type}","{appointment.appointment_date}","{appointment.appointment_time}","{appointment.specialty}","{appointment.action}"\n'
        output.write(row)
    
    output.seek(0)  # Reset the stream position to the beginning
    
    # Convert StringIO to BytesIO for Flask's send_file
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    # Return the CSV as a file attachment with the correct MIME type
    return send_file(mem, mimetype='text/csv', download_name='appointments.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=1111)
