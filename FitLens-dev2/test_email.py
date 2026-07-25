from flask_mail import Mail, Message
from flask import Flask
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_EMAIL')
mail = Mail(app)

print("Testing Gmail SMTP configuration...")
print(f"MAIL_EMAIL: {os.getenv('MAIL_EMAIL')}")
if not os.getenv('MAIL_PASSWORD'):
    print("WARNING: MAIL_PASSWORD is missing in .env")
else:
    print("MAIL_PASSWORD is set.")

try:
    with app.app_context():
        msg = Message('FitLens Test', recipients=[os.getenv('MAIL_EMAIL')])
        msg.body = 'Email is working!'
        mail.send(msg)
        print('Email sent successfully!')
except Exception as e:
    print(f"Email failed: {e}")
