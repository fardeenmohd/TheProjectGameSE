#!/usr/bin/python
from socket import *  # Import socket module
from threading import *


class CommunicationServer:
    def __init__(self, host=gethostname(), port=1922):
        self.host = host
        self.port = port
        self.socket = socket()
        self.socket.bind((self.host, self.port))
        print("Starting server.")

    def listen(self):
        self.socket.listen(1)  # Now wait for client connection.
        while True:
            client, address = self.socket.accept()
            print("New client with address " + str(address) + " connected.")
            client.settimeout(10)
            Thread(target=self.listen_to_client, args=(client, address)).start()

    def listen_to_client(self, client, address):
        buffer_size = 1024
        message = "Welcome to my server :)"
        client.send(message.encode())

        while True:
            try:
                received_data = client.recv(buffer_size)
                print("Received: "+received_data.decode())
                if received_data:
                    print("helo")
                    response = ("Your message was: "+received_data).encode()
                    client.send(response)
                else:
                    raise error('Client disconnected')
            except:
                client.close()
                return False

        client.close()

def run():
    server = CommunicationServer()
    server.listen()

run()
