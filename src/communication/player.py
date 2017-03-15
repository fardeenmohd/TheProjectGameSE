#!/usr/bin/env python
from socket import *
import datetime

DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = 420


class player:
    """Represents a player"""
    socket
    id

    def __init_(self, hostname=DEFAULT_HOSTNAME, port=DEFAULT_PORT):
        self.hostname = DEFAULT_HOSTNAME
        self.port = DEFAULT_PORT

    def connect(self):
        print("Creating a socket:" + datetime.datetime.now + "\n")
        player.socket = socket()

        while not socket.connect(self.hostname, self.port):
            print("Trying to connect to the humble server:" + datetime.datetime.now + "\n")
            if socket.connect(self.hostname, self.port):
                print("Connected to the humble server:" + datetime.datetime.now + "\n")
                received = socket.recv(1024)
                player.id = received.decode()

    def validate_type(given_type):
        return True

    def play(self):
        while True:
            try:
                print("Please enter message type:")
                message = input()
                if self.validate_type(message):
                    socket.send(message)
                else:
                    print("Please write a valid message type:")
                    message.input()
            except socket.timeout:
                print("Disconnected from the humble server \n")
                self.socket.close
