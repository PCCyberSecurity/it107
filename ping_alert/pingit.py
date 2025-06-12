import time
from ping3 import ping
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURATION ===

IP_ADDRESS = "192.168.8.81"  # Change to the IP or hostname you want to monitor
PING_INTERVAL = 60  # seconds

# Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use App Password for Gmail
RECIPIENT_EMAIL = "recipient_email@example.com"

# === FUNCTIONS ===

def send_email_alert(ip):
    subject = f"[ALERT] Ping Failed to {ip}"
    body = f"The ping to {ip} has failed. Host is unreachable."

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"ALERT: Email sent to {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def monitor_ping(ip):
    print(f"Starting ping monitor for {ip} every {PING_INTERVAL} seconds.")
    while True:
        try:
            delay = ping(ip, timeout=2)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if delay is None:
                print(f"[{timestamp}] Ping to {ip} failed (timeout).")
                send_email_alert(ip)
            else:
                print(f"[{timestamp}] Ping successful: {round(delay * 1000, 2)} ms")

        except Exception as e:
            print(f"Error pinging {ip}: {e}")
            send_email_alert(ip)

        time.sleep(PING_INTERVAL)

# === MAIN ===
if __name__ == '__main__':
    monitor_ping(IP_ADDRESS)
