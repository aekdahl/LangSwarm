# --- SMTPEmailSender.py (enhanced version) ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

class SMTPEmailSender:
    def __init__(self, smtp_server, smtp_port, username, password, from_email=None, use_tls=True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email or username
        self.use_tls = use_tls

    def send_email(self, to_email: str, subject: str, body: str, html_body: str = None, attachments: list = None):
        """
        Send an email.

        :param to_email: Recipient email address
        :param subject: Subject of the email
        :param body: Plain text body
        :param html_body: (Optional) HTML body
        :param attachments: (Optional) List of file paths to attach
        """
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach plain text body
        msg.attach(MIMEText(body, 'plain'))

        # Attach optional HTML body
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))

        # Attach optional files
        if attachments:
            for filepath in attachments:
                filename = os.path.basename(filepath)
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

"""
            
# Example:
sender = SMTPEmailSender(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your_email@gmail.com",
    password="your_app_password"  # Use Gmail App Password, not your real password
)

sender.send_email(
    to_email="recipient@example.com",
    subject="Hello from Gmail",
    body="This is a test email from your agent!"
)

# Notes for Gmail:

#You must enable App Passwords (not your main password) if you have 2FA enabled.
#Gmail SMTP requires TLS (use_tls=True by default).

# Example
sender = SMTPEmailSender(
    smtp_server="smtp.office365.com",
    smtp_port=587,
    username="your_email@outlook.com",
    password="your_password"
)

sender.send_email(
    to_email="recipient@example.com",
    subject="Hello from Outlook",
    body="This is a test email from your agent!"
)

# Notes for Outlook:

# Same as Gmail: SMTP server = smtp.office365.com, port = 587, TLS enabled.


# Example:
sender = SMTPEmailSender(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your_email@gmail.com",
    password="your_app_password"
)

sender.send_email(
    to_email="recipient@example.com",
    subject="Hello with HTML",
    body="This is the plain text version.",
    html_body="<h1>Hello!</h1><p>This is an HTML email sent by your agent.</p>"
)

# Attachment
sender.send_email(
    to_email="recipient@example.com",
    subject="Here is your file",
    body="Please find the attached document.",
    attachments=["/path/to/your/file.pdf"]
)

# Multiple attachments?
#Just pass a list:

# attachments=["/path/file1.pdf", "/path/file2.png"]

"""