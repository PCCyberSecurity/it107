import socket
import threading

# Function to handle each client connection
def handle_client(client_socket):
    # When the client sends a message, echo it back
    while True:
        try:
            # Receive data from the client (1024 bytes maximum)
            message = client_socket.recv(1024)
            if not message:
                break  # If no message, close the connection
            print(f"Received message: {message.decode('utf-8')}")
            # Send the message back to the client
            client_socket.send(message)
        except Exception as e:
            print(f"Error: {e}")
            break

    # Close the client connection
    client_socket.close()

# Main function to set up the server
def start_server(host='127.0.0.1', port=65432):
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Max backlog of 5 connections

    print(f"Server started on {host}:{port}")

    while True:
        # Accept a new connection
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")

        # Start a new thread to handle the client's messages
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Start the server
if __name__ == "__main__":
    start_server()
