import tkinter as tk
from tkinter import ttk, messagebox
import requests
import sqlite3
import threading
import time
import datetime
from ping3 import ping #, exceptions
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from dotenv import load_dotenv
import keyring
import pystray
from PIL import Image
import csv

# Load environment variables
load_dotenv()

# ===== Email Configuration =====
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = keyring.get_password("email", EMAIL_SENDER)

# ===== Database Setup =====
conn = sqlite3.connect('monitor.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS monitor_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target TEXT,
        type TEXT,
        timestamp DATETIME,
        status TEXT,
        latency REAL
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS monitor_targets (
        target TEXT PRIMARY KEY,
        type TEXT,
        email TEXT,
        delay INTEGER
    )
''')
conn.commit()

# ===== Global State =====
targets = {}
alert_cache = {}

# ===== Monitoring Functions =====
def save_result(target, monitor_type, status, latency):
    c.execute('''
        INSERT INTO monitor_results (target, type, timestamp, status, latency)
        VALUES (?, ?, ?, ?, ?)
    ''', (target, monitor_type, datetime.datetime.now(), status, latency))
    conn.commit()

def send_email_alert(target, monitor_type, status):
    recipient = targets[target]["email"]
    if not recipient:
        return

    subject = f"[ALERT] {monitor_type} Failure - {target}"
    body = f"Target: {target}\nType: {monitor_type}\nStatus: {status}\nTime: {datetime.datetime.now()}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Alert sent for {target}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def monitor_website(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=5, allow_redirects=True)
        latency = (time.time() - start) * 1000
        status = 'OK' if response.status_code in range(200, 400) else f"Bad ({response.status_code})"
    except Exception as e:
        latency = None
        status = f"Error: {str(e)}"

    save_result(url, "HTTP", status, latency)
    last_status = alert_cache.get(url)
    if status != 'OK' and last_status != status:
        send_email_alert(url, "HTTP", status)
    alert_cache[url] = status

def monitor_ping(host):
    try:
        latency = ping(host, timeout=2)
        if latency is not None:
            latency *= 1000
            status = 'OK'
        else:
            status = 'Timeout'
    # except exceptions.PingError as e:
    #     latency = None
    #     status = f"PingError: {str(e)}"
    except Exception as e:
        latency = None
        status = f"Error: {type(e).__name__}: {str(e)}"

    save_result(host, "PING", status, latency)
    last_status = alert_cache.get(host)
    if status != 'OK' and last_status != status:
        send_email_alert(host, "PING", status)
    alert_cache[host] = status

def start_monitoring():
    def run():
        while True:
            for target, settings in targets.items():
                if settings["type"] == "HTTP":
                    monitor_website(target)
                elif settings["type"] == "PING":
                    monitor_ping(target)
            time.sleep(60)
    threading.Thread(target=run, daemon=True).start()

# ===== GUI Functions =====
def load_targets():
    c.execute("SELECT target, type, email, delay FROM monitor_targets")
    for target, ttype, email, delay in c.fetchall():
        targets[target] = {
            "type": ttype,
            "email": email,
            "delay": delay
        }
        target_listbox.insert(tk.END, target)

def add_target():
    target = target_entry.get()
    if target and target not in targets:
        target_type = type_combobox.get()
        email = email_entry.get()
        delay = int(delay_entry.get() or 60)

        targets[target] = {
            "type": target_type,
            "email": email,
            "delay": delay
        }
        c.execute('''
            INSERT OR REPLACE INTO monitor_targets (target, type, email, delay)
            VALUES (?, ?, ?, ?)
        ''', (target, target_type, email, delay))
        conn.commit()

        target_listbox.insert(tk.END, target)
        target_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        delay_entry.delete(0, tk.END)

def show_latency_graph():
    target = graph_target_entry.get()
    if not target:
        messagebox.showwarning("Input needed", "Enter a target to graph")
        return
    c.execute('''
        SELECT timestamp, latency FROM monitor_results
        WHERE target = ? AND latency IS NOT NULL
        ORDER BY timestamp ASC
    ''', (target,))
    data = c.fetchall()
    if not data:
        messagebox.showinfo("No data", f"No data found for {target}")
        return

    times = [datetime.datetime.fromisoformat(row[0]) for row in data]
    latencies = [row[1] for row in data]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(times, latencies, marker='o')
    ax.set_title(f'Latency for {target}')
    ax.set_ylabel('Latency (ms)')
    ax.set_xlabel('Time')
    ax.grid(True)

    top = tk.Toplevel(root)
    top.title(f'Latency Graph - {target}')
   
    canvas = FigureCanvasTkAgg(fig, master=top)
    canvas.draw()
    canvas.get_tk_widget().pack()



def export_to_csv():
    c.execute('SELECT * FROM monitor_results')
    rows = c.fetchall()
    with open('monitor_results.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([desc[0] for desc in c.description])
        writer.writerows(rows)
    messagebox.showinfo("Export", "Data exported to monitor_results.csv")

def quit_window(icon, item):
    icon.stop()
    root.destroy()

def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)

def minimize_to_tray():
    root.withdraw()
    image = Image.new("RGB", (64, 64), "blue")  # Placeholder icon
    menu = pystray.Menu(
        pystray.MenuItem("Show", show_window),
        pystray.MenuItem("Quit", quit_window)
    )
    icon = pystray.Icon("MonitorApp", image, "Monitor Running", menu)
    threading.Thread(target=icon.run, daemon=True).start()

root = tk.Tk()
root.title("Website & Host Monitor")

tk.Label(root, text="Target URL/IP").grid(row=0, column=0)
target_entry = tk.Entry(root, width=30)
target_entry.grid(row=0, column=1)

tk.Label(root, text="Type").grid(row=1, column=0)
type_combobox = ttk.Combobox(root, values=["HTTP", "PING"])
type_combobox.current(0)
type_combobox.grid(row=1, column=1)

tk.Label(root, text="Email").grid(row=2, column=0)
email_entry = tk.Entry(root, width=30)
email_entry.grid(row=2, column=1)

tk.Label(root, text="Delay (sec)").grid(row=3, column=0)
delay_entry = tk.Entry(root, width=30)
delay_entry.insert(0, "60")
delay_entry.grid(row=3, column=1)

tk.Button(root, text="Add Target", command=add_target).grid(row=4, column=1)

target_listbox = tk.Listbox(root, width=50)
target_listbox.grid(row=5, column=0, columnspan=2, pady=10)

tk.Label(root, text="Graph Target").grid(row=6, column=0)
graph_target_entry = tk.Entry(root)
graph_target_entry.grid(row=6, column=1)

tk.Button(root, text="Show Graph", command=show_latency_graph).grid(row=7, column=0)
tk.Button(root, text="Export CSV", command=export_to_csv).grid(row=7, column=1)
tk.Button(root, text="Minimize to Tray", command=minimize_to_tray).grid(row=8, column=0, columnspan=2)

load_targets()
start_monitoring()
root.mainloop()
