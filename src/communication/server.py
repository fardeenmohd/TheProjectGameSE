#!/usr/bin/python
import socket, sys
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from time import sleep


class CommunicationServer:
    # some constants:
    INTER_PRINT_STATE_TIME = 5
    DEFAULT_BUFFER_SIZE = 1024
    DEFAULT_PORT = 420
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
        self.running = True
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
        Thread(target=self.print_state, daemon=True).start()
        Thread(target=self.accept_clients, daemon=True).start()

        try:
            while self.running:
                text = input()

                if text == "stop" or text == "close":
                    raise KeyboardInterrupt

                if text == "state":
                    self.verbose_debug("Currently there are " + str(self.clientCount) + " clients connected.", True)

                if text == "clients":
                    self.verbose_debug("Currently connected clients:", True)
                    if len(self.playerDict) > 0:
                        for player in self.playerDict:
                            print(" P" + player+": "+self.playerDict[player])
                    else:
                        print(" There are no currently connected clients.")

        except KeyboardInterrupt:
            self.verbose_debug("Server closed by user.", True)
            self.socket.close()
            sys.exit(0)

    def accept_clients(self):
        player_id = 0
        while self.running:
            sock, address = self.socket.accept()
            if self.clientCount < CommunicationServer.DEFAULT_CLIENT_LIMIT:
                new_id = player_id
                self.playerDict[new_id] = sock
                self.clientCount += 1
                player_id += 1

                self.verbose_debug(
                    "New client with address " + str(address) + "and id " + str(new_id) + " connected.",
                    True)
                thread = Thread(target=self.handle_player, args=(sock, new_id))
                thread.daemon = True
                thread.start()
            sleep(1)

    def print_state(self):
        while self.running:
            self.verbose_debug("Currently there are " + str(self.clientCount) + " clients connected.")
            sleep(CommunicationServer.INTER_PRINT_STATE_TIME)

    def handle_player(self, client, player_id):
        buffer_size = CommunicationServer.DEFAULT_BUFFER_SIZE
        message = player_id
        client.send(str(message).encode())
        self.verbose_debug("Sent id to player " + str(player_id))

        while self.running:
            try:
                received_data = client.recv(buffer_size).decode()
                self.verbose_debug("Received: \"" + received_data + "\" from player" + str(player_id))

                response = ("Your message was: " + str(received_data))
                client.send(response.encode())
                self.verbose_debug("Sent: \"" + response + "\" to player " + str(player_id))

            except ConnectionAbortedError:
                self.verbose_debug(
                    "Player " + str(player_id) + " disconnected. Closing connection.", True)
                client.close()
                self.clientCount -= 1
                return False

            except socket.error as e:
                self.verbose_debug(
                    "Closing connection with Player " + str(player_id) + " due to a socket error: " + str(e) + ".",
                    True)
                client.close()
                self.clientCount -= 1
                return False

            except Exception as e:
                self.verbose_debug("Unexpected exception: " + str(e) + ".", True)
                raise e

    def shutdown(self):
        self.running = False
        socket.socket(socket.AF_INET,
                      socket.SOCK_STREAM).connect((self.DEFAULT_HOSTNAME, self.DEFAULT_PORT))
        self.socket.close()

if __name__ == '__main__':
    def run(verbose):
        server = CommunicationServer(verbose)
        server.listen()


    try:
        parser = ArgumentParser()
        parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
        args = vars(parser.parse_args())
        run(args["verbose"])
    except KeyboardInterrupt:
        print("AHMADABAD")
