#!/usr/bin/env python
import socket
import time
import threading
from datetime import datetime


class Player:
    """Represents a player (a client)"""
    TIME_INTER_CONNECTION = 10
    DEFAULT_HOSTNAME = socket.gethostname() #localhost
    DEFAULT_PORT = 4000
    DEFAULT_MESSAGE_BUFFER_SIZE = 1024

    def __init__(self, index, verbose):
        # initialize client's fields to default values
        self.hostname = Player.DEFAULT_HOSTNAME
        self.port = Player.DEFAULT_PORT
        self.socket = socket.socket()
        self.index = index  # local index used to differentiate between players running in threads
        self.id = None  # id used to communicate with server
        self.verbose = verbose  # if yes, there will be a lot of output printed out
        if self.verbose:
            self.print_debug("Player successfully created.")

    def connect(self):
        if self.verbose:
            self.print_debug("Creating a socket")

        while True:
            try:
                if self.verbose:
                    self.print_debug("Trying to connect to server...")
                self.socket.connect((self.hostname, self.port))
                if self.verbose:
                    self.print_debug("Connected to server.")
                received = self.socket.recv(Player.DEFAULT_MESSAGE_BUFFER_SIZE)
                self.id = received.decode()
                print(self.id)
                return

            except socket.error:
                if self.verbose:
                    self.print_debug("Connecting to server failed. Trying again in "+Player.TIME_INTER_CONNECTION)
                time.sleep(Player.TIME_INTER_CONNECTION)
                continue

                # def validate_type(self ,given_type):
                # return True

    def play(self):
        while True:
            try:
                time.sleep(5)
                message = "Hello server."
                # if self.validate_type(self, message):
                socket.socket.send(self.socket, message.encode())
                received_data = self.socket.recv(1024)
                # print(str(datetime.now().time()) + " - received from server: " + received_data.decode())
                if self.verbose:
                    self.print_debug("Received from server:"+ str(received_data).decode())
                if message == "close":
                    self.socket.close()
                    if self.verbose:
                        self.print_debug("Disconnected. ")

                        # else:
                    # print("Please write a valid message type:")

            except ConnectionAbortedError:
                self.socket.close()
                if self.verbose:
                    self.print_debug("Disconnected from server.")
                return

    def print_debug(self, message):
        header = "Player " + str(self.index) + " at " + str(datetime.now().time()) + " - "
        print(header, message)


def run(number_of_players, verbose):
    for i in range(number_of_players):
        threading.Thread(target=create_player, args=(i + 1, verbose)).start()


def create_player(index, verbose=True):
    p = Player(index, verbose)
    p.connect()
    p.play()


run(3, True)
