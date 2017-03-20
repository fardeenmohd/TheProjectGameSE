#!/usr/bin/python
import socket
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from time import sleep


class CommunicationServer:
    INTER_PRINT_STATE_TIME = 5
    DEFAULT_BUFFER_SIZE = 1024
    DEFAULT_PORT = 8000
    DEFAULT_TIMEOUT = 10
    DEFAULT_CLIENT_LIMIT = 10
    DEFAULT_HOSTNAME = socket.gethostname()

    def __init__(self, verbose, host=DEFAULT_HOSTNAME, port=DEFAULT_PORT):
        """
        constructor.
        :param verbose:
        :param host:
        :param port:
        """
        self.socket = socket.socket()
        self.playerDict = {}
        self.clientCount = 0
        self.verbose = verbose
        self.socket.bind((host, port))
        # self.socket.settimeout(CommunicationServer.DEFAULT_TIMEOUT)
        self.verbose_debug("Created server with hostname: " + host + " on port " + str(port), important=True)

    def verbose_debug(self, message, important=False):
        """
        if in verbose mode, print out the given message with a timestamp
        :param message: message to be printed
        """
        if self.verbose or important:
            header = "S" + " at " + str(datetime.now().time()) + " - "
            print(header, message)

    def listen(self):
        """
        accept client connections and deploy threads.
        """
        self.socket.listen()
        self.verbose_debug("Started listening")
        Thread(target=self.print_state).start()
        player_id = 0

        while True:
            if self.clientCount < CommunicationServer.DEFAULT_CLIENT_LIMIT:
                socket, address = self.socket.accept()
                new_id = player_id
                self.playerDict[new_id] = socket
                self.clientCount += 1
                player_id += 1

                self.verbose_debug("New client with address " + str(address) + "and id " + str(new_id) + " connected.",
                                   True)
                Thread(target=self.handle_player, args=(socket, new_id)).start()
            else:
                sleep(1)

    def print_state(self):
        while True:
            self.verbose_debug("Currently there are " + str(self.clientCount) + " clients connected.")
            sleep(CommunicationServer.INTER_PRINT_STATE_TIME)

    def handle_player(self, client, player_id):
        buffer_size = CommunicationServer.DEFAULT_BUFFER_SIZE
        message = player_id
        client.send(str(message).encode())
        self.verbose_debug("Sent id to player " + str(player_id))

        while True:
            try:
                received_data = client.recv(buffer_size).decode()
                self.verbose_debug("Received: \"" + received_data + "\" from player" + str(player_id))

                response = ("Your message was: " + str(received_data))
                client.send(response.encode())
                self.verbose_debug("Sent: \"" + response + "\" to player " + str(player_id))

            except socket.error:
                self.verbose_debug(
                    "Player " + str(player_id) + " disconnected (or connection error). Closing connection.",
                    important=True)
                client.close()
                self.clientCount -= 1
                return False


def run(verbose):
    server = CommunicationServer(verbose)
    server.listen()


parser = ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
args = vars(parser.parse_args())
run(args["verbose"])
