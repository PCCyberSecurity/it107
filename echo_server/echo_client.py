import socket

# Function to handle sending and receiving messages
def communicate_with_server(host='127.0.0.1', port=65432):
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect the client to the server
        client_socket.connect((host, port))

        print(f"Connected to server at {host}:{port}")

        while True:
            # Get user input to send to the server
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == 'exit':
                print("Exiting...")
                break

            # Send the message to the server
            client_socket.sendall(message.encode('utf-8'))

            # Receive the echo response from the server
            response = client_socket.recv(1024)
            print(f"Received from server: {response.decode('utf-8')}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Close the socket connection
        client_socket.close()

if __name__ == "__main__":
    communicate_with_server()
