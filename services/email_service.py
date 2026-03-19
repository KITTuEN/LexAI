import smtplib
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_sender = os.getenv('SMTP_SENDER')

    def generate_otp(self):
        return "".join([str(random.randint(0, 9)) for _ in range(6)])

    def send_otp_email(self, receiver_email, otp):
        try:
            msg = MIMEMultipart()
            msg['From'] = f"LexAI Support <{self.smtp_sender}>"
            msg['To'] = receiver_email
            msg['Subject'] = "Your LexAI Verification Code"

            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="background-color: #ffffff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                        <h2 style="color: #B8860B; text-align: center;">LexAI Verification</h2>
                        <p style="font-size: 16px; color: #333;">Welcome to LexAI. Use the following 6-digit code to verify your account:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #05070A; background: #f0f0f0; padding: 10px 20px; border-radius: 5px;">{otp}</span>
                        </div>
                        <p style="font-size: 14px; color: #777;">This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">&copy; 2026 LexAI - Indian Legal Empowerment</p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

email_service = EmailService()
