#!/usr/bin/env python
from socket import *
import datetime
import time

DEFAULT_HOSTNAME = gethostname()
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

        while True:
            try:
                print(datetime.datetime.now().time())
                print(":Trying to connect to the humble server")
                socket.connect(self.socket, (self.hostname, self.port))
                print(datetime.datetime.now().time())
                print(":Connected to the humble server")
                received = socket.recv(self.socket, 1024)
                self.id = received.decode()
                return

            except error:
                print(datetime.datetime.now().time())
                print("FAILED. Sleep briefly & try again")
                time.sleep(10)
                continue

    def validate_type(self, given_type):
        return True

    def play(self):
        while True:
            try:
                print("Please enter message type:")
                message = input()
                if self.validate_type(message):
                    socket.send(self.socket, message.encode())
                elif message == "close":
                    self.socket.close()
                else:
                    print("Please write a valid message type:")
            except timeout:
                print(datetime.datetime.now().time())
                print(":Disconnected from the humble server ")
                self.socket.close()

p = player()
p.connect()
p.play()

