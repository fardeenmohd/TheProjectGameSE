#!/usr/bin/python
from socket import *  # Import socket module
from threading import *

DEFAULT_PORT = 420
DEFAULT_TIMEOUT = 10
DEFAULT_CLIENT_LIMIT = 10


class CommunicationServer:

    def __init__(self, host=gethostname(), port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = socket()
        self.socket.bind((self.host, self.port))
        self.playerDict = {}
        print("Starting server with hostname: ", self.host, " and on port ", self.port)

    def listen(self):
        self.socket.listen(1)  # Now wait for client connection.
        player_id = 0
        while True:
            client, address = self.socket.accept()
            print("New client with address " + str(address) + " connected.")
            self.playerDict[player_id] = client
            player_id += 1
            client.settimeout(DEFAULT_TIMEOUT)
            Thread(target=self.handle_player, args=(client, address, player_id)).start()

    def handle_player(self, client, address, player_id):
        buffer_size = 1024
        message = player_id
        client.send(str(message).encode())

        while True:
            try:
                received_data = client.recv(buffer_size).decode()
                print("Server Received: " + received_data)
                response = ("Your message was: " + str(received_data))
                client.send(response.encode())

            except error:
                client.close()
                return False


def run():
    server = CommunicationServer()
    server.listen()

run()
