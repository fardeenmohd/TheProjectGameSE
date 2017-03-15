#!/usr/bin/env python
from socket import *
import datetime

DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = 420


class player:
    """Represents a player"""

    def __init__(self):
        self.hostname = DEFAULT_HOSTNAME
        self.port = DEFAULT_PORT


    def connect(self):
        print(datetime.datetime.now().time())
        print(":Creating a socket\n")
        self.socket = socket()
        self.socket.settimeout(100000)

        while not socket.connect(self.socket,(self.hostname, self.port)):
            print(datetime.datetime.now().time())
            print(":Trying to connect to the humble server\n")
            if socket.connect(self,(self.hostname, self.port)):
                print(datetime.datetime.now().time())
                print(":Connected to the humble server\n")
                received = socket.recv(1024)
                self.id = received.decode()

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
                print(datetime.datetime.now().time())
                print(":Disconnected from the humble server \n")
                self.socket.close

p = player()
p.connect()

