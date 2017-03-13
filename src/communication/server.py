#!/usr/bin/python
from socket import *           # Import socket module

socket = socket()         # Create a socket object
host = gethostname()    # Get local machine name
port = 6969                # Reserve a port for your service.
socket.bind((host, port))        # Bind to the port

print("Starting server.")

socket.listen(1)                 # Now wait for client connection.
c, addr = socket.accept()     # Establish connection with client.
print(c)
message = "Welcome to my humble server."
c.send(message.encode())
c.close()                # Close the connection

print("Shutting down server.")