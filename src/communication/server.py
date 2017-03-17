#!/usr/bin/python
import socket
import threading
import time
from datetime import datetime


class CommunicationServer:
    DEFAULT_BUFFER_SIZE = 1024
    DEFAULT_PORT = 4000
    DEFAULT_TIMEOUT = 10
    DEFAULT_CLIENT_LIMIT = 10

    def __init__(self, verbose):
        self.host = socket.gethostname() # LOCALHOST
        self.port = CommunicationServer.DEFAULT_PORT
        self.socket = socket.socket()
        self.socket.bind((self.host, self.port))
        self.playerDict = {}
        self.clientCount = 0
        self.verbose = verbose
        print("Starting server with hostname: ", self.host, " and on port ", self.port)

    def listen(self):
        self.socket.listen()
        threading.Thread(target=self.print_state).start()
        print("Started listening")
        player_id = 0
        while True:
            if self.clientCount < CommunicationServer.DEFAULT_CLIENT_LIMIT:
                client, address = self.socket.accept()
                print("New client with address " + str(address) + " connected.")
                self.playerDict[player_id] = client
                self.clientCount += 1
                player_id += 1
                client.settimeout(CommunicationServer.DEFAULT_TIMEOUT)
                threading.Thread(target=self.handle_player, args=(client, address, player_id)).start()
            else:
                time.sleep(1)

    def print_state(self):
        while True:
            print(datetime.now().time(), ": Currently there are ", self.clientCount, " clients connected")
            time.sleep(5)

    def handle_player(self, client, address, player_id):
        buffer_size = CommunicationServer.DEFAULT_BUFFER_SIZE
        message = player_id
        client.send(str(message).encode())

        while True:
            try:
                received_data = client.recv(buffer_size).decode()
                print("Server Received: " + received_data)
                response = ("Your message was: " + str(received_data))
                client.send(response.encode())

            except socket.error:
                client.close()
                self.clientCount -= 1
                return False


def run(verbose):
    server = CommunicationServer(verbose)
    server.listen()


run(True)
