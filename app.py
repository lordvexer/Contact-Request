from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime
import csv
import uuid
from flask import session


ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '24122412'

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# -----------------------
# DATABASE
# -----------------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    phone_numbers TEXT NOT NULL,
                    birthdate TEXT NOT NULL,
                    email TEXT,
                    image_path TEXT
                )''')
    conn.commit()
    conn.close()

# -----------------------
# HELPERS
# -----------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------
# ROUTES
# -----------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birthdate = request.form['DatePickerHidden']
        email = request.form.get('email')
        phone_numbers = request.form.getlist('phone_numbers[]')
        profile_image = request.files['profile_image']

        if not first_name.isascii() or not last_name.isascii():
            flash('First and Last names must be in English only.')
            return redirect(url_for('index'))

        if not first_name or not last_name or not birthdate or not phone_numbers[0]:
            flash('Please fill in all required fields.')
            return redirect(url_for('index'))

        try:
            datetime.strptime(birthdate, '%Y-%m-%d')
        except ValueError:
            flash('Invalid birthdate format. Use YYYY-MM-DD.')
            return redirect(url_for('index'))

        filename = None
        if profile_image and allowed_file(profile_image.filename):
            unique_name = str(uuid.uuid4()) + "_" + secure_filename(profile_image.filename)
            filename = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            profile_image.save(filename)

        phone_combined = ','.join(phone_numbers)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT id FROM users WHERE phone_numbers LIKE ?", (f"%{phone_numbers[0]}%",))
        result = c.fetchone()

        if result:
            user_id = result[0]
            c.execute('''UPDATE users SET first_name=?, last_name=?, phone_numbers=?, birthdate=?, email=?, image_path=? WHERE id=?''',
                      (first_name, last_name, phone_combined, birthdate, email, filename, user_id))
        else:
            c.execute('''INSERT INTO users (first_name, last_name, phone_numbers, birthdate, email, image_path)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (first_name, last_name, phone_combined, birthdate, email, filename))
        conn.commit()
        conn.close()

        flash('Your information has been saved successfully!')
        return redirect(url_for('index'))

    return render_template('form.html')


@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    users = [
        {
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'phone_numbers': row[3].split(','),
            'birthdate': row[4],
            'email': row[5],
            'image_path': row[6]
        }
        for row in users
    ]

    return render_template('admin.html', contacts=users)



@app.route('/export_csv')
def export_csv():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()

    filename = 'all_contacts.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Given Name', 'Family Name', 'Phone 1 - Value', 'Phone 2 - Value', 'E-mail 1 - Value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            phones = row[3].split(',')
            writer.writerow({
                'Name': row[1] + ' ' + row[2],
                'Given Name': row[1],
                'Family Name': row[2],
                'Phone 1 - Value': phones[0] if phones else '',
                'Phone 2 - Value': phones[1] if len(phones) > 1 else '',
                'E-mail 1 - Value': row[5] or ''
            })

    return send_file(filename, as_attachment=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid credentials.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out.')
    return redirect(url_for('login'))



    # همانند قبل: گرفتن اطلاعات از دیتابیس

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_numbers = ','.join(request.form.getlist('phone_numbers[]'))
        birthdate = request.form['DatePickerHidden']
        email = request.form['email']
        c.execute('''UPDATE users SET first_name=?, last_name=?, phone_numbers=?, birthdate=?, email=? WHERE id=?''',
                  (first_name, last_name, phone_numbers, birthdate, email, user_id))
        conn.commit()
        conn.close()
        flash('User updated successfully.')
        return redirect(url_for('admin_panel'))

    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        user_data = {
            'id': user[0],
            'first_name': user[1],
            'last_name': user[2],
            'phone_numbers': user[3].split(','),
            'birthdate': user[4],
            'email': user[5],
        }
        return render_template('edit_user.html', user=user_data)
    else:
        flash('User not found.')
        return redirect(url_for('admin_panel'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted.')
    return redirect(url_for('admin_panel'))



# -----------------------
# START APP
# -----------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
