import io
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, send_file ,jsonify,render_template_string, g, session, send_from_directory,url_for
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime , timedelta
import csv
import uuid
from flask import session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jdatetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import tempfile


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///licenses.db'
app.config['SECRET_KEY'] = '256556654'







# تنظیمات لاگ برای چاپ در کنسول
logging.basicConfig(level=logging.DEBUG)
# در ابتدای فایل app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'database', 'database.db')


ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '24122412'

app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# -----------------------
# DATABASE
# -----------------------
def init_db():

    # اگر متغیر محیطی DB_PATH تنظیم شده بود، از آن استفاده کن (برای cPanel)
    db_path = os.environ.get('DB_PATH')

    if not db_path:
        # در لوکال: از مسیر نسبی به فولدر database استفاده کن
        db_path = os.path.join(os.path.dirname(BASE_DIR), 'database', 'database.db')

    # اطمینان از اینکه فولدر database وجود دارد
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # ایجاد جدول users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone_numbers TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            email TEXT,
            image_path TEXT
        )
    ''')

    # ایجاد جدول settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adjust_day INTEGER NOT NULL
        )
    ''')

    # بررسی مقدار اولیه
    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (adjust_day) VALUES (0)")

    conn.commit()
    conn.close()
    print(f"📂 Database path: {db_path}")




@app.route('/update_settings', methods=['GET', 'POST'])
def update_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        logging.debug("GET request received for update_settings.")

        try:
            # اتصال به دیتابیس و خواندن مقدار adjust_day از تنظیمات
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT adjust_day FROM settings WHERE id=1;")
            row = c.fetchone()  # گرفتن مقدار اولین رکورد

            # بررسی و لاگ گرفتن از نتیجه
            if row:
                adjust_day = row[1]  # اگر رکورد وجود داشت
                logging.debug(f"Current adjust_day value from DB: {adjust_day}")
            else:
                adjust_day = 0  # اگر رکوردی نبود مقدار پیش‌فرض 0
                logging.debug("No record found for settings, using default adjust_day = 0.")

            conn.close()

        except Exception as e:
            logging.error(f"Error reading from database: {e}")
            adjust_day = 0  # در صورت بروز خطا، مقدار پیش‌فرض 0

        # ارسال مقدار به قالب برای نمایش
        return render_template('settings.html', adjust_day=adjust_day)

    elif request.method == 'POST':
        adjust_day = request.form['adjust_day']
        logging.debug(f"POST request received. Adjust day value to update: {adjust_day}")

        # اتصال به دیتابیس و بروزرسانی تنظیمات
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE settings SET adjust_day=? WHERE id=1", (adjust_day,))
        conn.commit()
        conn.close()

        logging.debug(f"adjust_day value updated to {adjust_day} in DB.")

        flash('Settings updated successfully!')
        return redirect(url_for('admin_panel'))





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
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birthdate = request.form.get('DatePickerHidden')
        email = request.form.get('email')
        phone_numbers = request.form.getlist('phone_numbers[]')
        profile_image = request.files.get('profile_image')

        if not first_name or not last_name or not birthdate or not phone_numbers or not phone_numbers[0]:
            flash('Please fill in all required fields.')
            return redirect(url_for('index'))

        if not first_name.isascii() or not last_name.isascii():
            flash('First and Last names must be in English only.')
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

        conn = sqlite3.connect(DB_PATH)
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

    conn = sqlite3.connect(DB_PATH)
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




def persian_to_english_digits(s):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    table = str.maketrans(''.join(persian_digits), ''.join(english_digits))
    return s.translate(table)

import tempfile

@app.route('/export_csv')
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', dir='.')
    filename = temp_file.name

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Given Name', 'Family Name', 'Phone 1 - Value', 'Phone 2 - Value', 'E-mail 1 - Value', 'Birthday (Gregorian)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            phones = row[3].split(',')

            try:
                shamsi_raw = row[4]
                shamsi_clean = persian_to_english_digits(shamsi_raw)
                parts = shamsi_clean.split('-')
                j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                g_date = j_date.togregorian().strftime('%Y-%m-%d')
            except Exception as e:
                g_date = ''

            writer.writerow({
                'Name': row[1] + ' ' + row[2],
                'Given Name': row[1],
                'Family Name': row[2],
                'Phone 1 - Value': phones[0] if phones else '',
                'Phone 2 - Value': phones[1] if len(phones) > 1 else '',
                'E-mail 1 - Value': row[5] or '',
                'Birthday (Gregorian)': g_date
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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_numbers = ','.join(request.form.getlist('phone_numbers[]'))
        birthdate = request.form['birthdate']
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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted.')
    return redirect(url_for('admin_panel'))


import jdatetime

def jalali_to_gregorian(jalali_date):
    """تبدیل تاریخ شمسی به میلادی"""
    year, month, day = map(int, jalali_date.split('-'))
    jalali = jdatetime.date(year, month, day)
    gregorian = jalali.togregorian()
    return gregorian.strftime('%Y-%m-%d')  # تبدیل به فرمت میلادی و بازگشت آن

def check_birthdays_and_notify():
    print("📅 Checking upcoming birthdays...")

    # گرفتن تاریخ فردا
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%m-%d')
    print(f"🔍 Target date for matching: {tomorrow}")

    # اتصال به دیتابیس و گرفتن تنظیمات adjust_day
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT adjust_day FROM settings WHERE id=1")
    adjust_day = c.fetchone()[0]
    conn.close()

    # اگر adjust_day غیر صفر باشد، تاریخ هدف تغییر می‌کند
    if adjust_day != 0:
        tomorrow_date = datetime.strptime(tomorrow, '%m-%d') + timedelta(days=adjust_day)
        tomorrow = tomorrow_date.strftime('%m-%d')
        print(f"🔧 Adjusted target date for matching: {tomorrow}")

    # اتصال مجدد به دیتابیس و گرفتن اطلاعات کاربران
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT first_name, last_name, email, birthdate FROM users")
    users = c.fetchall()
    conn.close()

    print(f"👥 Total users found: {len(users)}")

    matching_users = []
    for user in users:
        if not user[3]:
            continue
        try:
            # اگر تاریخ شمسی بود، تبدیل به میلادی کنید
            if '۰' <= user[3][0] <= '۹':  # بررسی اینکه آیا تاریخ به فارسی است
                birthdate = jalali_to_gregorian(user[3])
            else:
                birthdate = user[3]
            
            birth_mmdd = datetime.strptime(birthdate, '%Y-%m-%d').strftime('%m-%d')
            if birth_mmdd == tomorrow:
                matching_users.append(user)
        except Exception as e:
            print(f"⛔ Error parsing birthdate for user {user}: {e}")
            continue

    # ارسال ایمیل به کاربران با تاریخ تولد فردا
    if matching_users:
        print(f"🎯 Users with birthdays tomorrow: {len(matching_users)}")
        message = "🎉 Birthday reminder for tomorrow:\n\n"
        for u in matching_users:
            full_name = f"{u[0]} {u[1]}"
            email = u[2] if u[2] else '—'
            birthdate = u[3]
            message += f"🎂 {full_name} (📧 {email}) - Birthdate: {birthdate}\n"
        print("✉️ Sending email notification...")
        send_email_notification(message)
    else:
        print("ℹ️ No birthdays found for tomorrow.")






def send_email_notification(body):
    sender_email = "remainder@rabinn.ir"
    receiver_email = "h.nypdv@gmail.com"  # جایگزین کنید با ایمیل مقصد
    password = "E6Dx#ZOF5zG+"  # رمز عبور ایمیل شما

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Birthday Reminder"

    msg.attach(MIMEText(body, 'plain'))

    try:
        print("🔌 Trying to connect to SMTP server...")
        with smtplib.SMTP_SSL("mail.rabinn.ir", 465) as server:
            #server.set_debuglevel(1)  # فعال کردن حالت دیباگ برای دیدن جزییات اتصال
            server.login(sender_email, password)  # ورود به سرور
            print("🔑 Login successful!")
            server.send_message(msg)  # ارسال ایمیل
        print("✉️ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email failed to send. Error: {e}")
# -----------------------
# START APP
# -----------------------
if __name__ == '__main__':
     init_db()
     app.run(debug=True)
