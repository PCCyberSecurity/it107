import socket
import threading
import sys
import time

# Config
# Server will listen on this port
LISTEN_PORT = 12345 # int(input("Enter your listen port (e.g., 12345): "))

# Sending packets out to the broadcast address (ALL users)
TARGET_IP = "255.255.255.255" # input("Enter peer IP (e.g., 255.255.255.255): ")
TARGET_PORT = 12345 # int(input("Enter peer port (e.g., 12346): "))

# Make the socket (Phone so we can call or listen)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Need to turn on broadcast capabilities
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# Allow more than one app to bind to the same socket
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
except AttributeError:
    pass # Not available in all systems - this is ok
except OSError:
    pass

# Tell our socket to listen on our port so we can see
# messages coming in
sock.bind(('0.0.0.0', LISTEN_PORT))

# Number of past messages to show
MAX_MESSAGES = 6
messages = []

def clear_terminal():
    print("\033c", end='')

def move_cursor(row, col):
    print(f"\033[{row};{col}H", end='')

def refresh_screen():
    clear_terminal()
    for i, msg in enumerate(messages[-MAX_MESSAGES:]):
        move_cursor(i + 1, 1)
        print(msg.ljust(80))  # pad to avoid line bleed
    move_cursor(MAX_MESSAGES + 2, 1)
    print("Type your message (or 'quit' to exit):")
    move_cursor(MAX_MESSAGES + 3, 1)
    print("> ", end='', flush=True)

def receive_messages():
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = f"[{addr[0]}:{addr[1]}] {data.decode()}"
            messages.append(msg)
            refresh_screen()
        except Exception as e:
            break

# Start listener thread so we can pickup messages
# coming in from ourselves or other users
threading.Thread(target=receive_messages, daemon=True).start()

# Initial UI draw
refresh_screen()

# Main loop for sending - capture message from user
# and broadcast it out to the world.
while True:
    move_cursor(MAX_MESSAGES + 3, 3)
    try:
        message = input()
        if message.lower() == "quit":
            break
        sock.sendto(message.encode(), (TARGET_IP, TARGET_PORT))
        # Optional: also show sent messages in the chat window
        messages.append(f"[Me -> {TARGET_IP}:{TARGET_PORT}] {message}")
        refresh_screen()
    except KeyboardInterrupt:
        break

sock.close()
print("\nDisconnected.")
