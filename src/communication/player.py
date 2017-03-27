#!/usr/bin/env python
import socket
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from time import sleep
import src.communication.messages as messages


class Player:
    TIME_BETWEEN_MESSAGES = 5  # time in s between each message sent by player
    INTER_CONNECTION_TIME = 3  # time in s between attemps to connect to server
    CONNECTION_ATTEMPTS = 3  # how many times the clients will retry the attempt to connect
    DEFAULT_HOSTNAME = "P21715"  # keep this as socket.gethostname() if you're debugging on your own pc
    DEFAULT_PORT = 4242
    MESSAGE_BUFFER_SIZE = 1024

    def __init__(self, index, verbose):
        """
        constructor.
        :param index: local index used to differentiate between different players running in threads
        :param verbose: boolean value. if yes, there will be a lot of output printed out.
        """
        self.interConnectionTime = Player.INTER_CONNECTION_TIME
        self.timeBetweenMessages = Player.TIME_BETWEEN_MESSAGES
        self.connectionAttempts = Player.CONNECTION_ATTEMPTS
        self.socket = socket.socket()
        self.index = index
        self.id = None  # will be assigned after connecting to gamemaster.
        self.verbose = verbose
        self.connected = False  # will be changed if connected
        self.last_message = None
        # self.socket.settimeout(1)

        self.verbose_debug("Player created.")

    def connect(self, hostname=DEFAULT_HOSTNAME, port=DEFAULT_PORT):
        """
        try to connect to server and receive UID
        :param hostname: host name to connect to
        :param port: port to connect to
        """
        failed_connections = 0

        while True:
            try:
                self.verbose_debug("Trying to connect to server " + str(hostname + " at port " + str(port) + "."))
                self.socket.connect((hostname,port))
                # try to receive the initial "greeting" byte from Server
                # received = self.socket.recv(1)

                # say hello to the server
                # self.send("1")
                self.connected = True
                return True

            except socket.error:
                if failed_connections < self.connectionAttempts:
                    failed_connections += 1
                    self.verbose_debug("Attempt number " + str(failed_connections) + " failed. Trying again in " + str(
                        self.interConnectionTime) + " seconds.")
                    sleep(self.interConnectionTime)
                    continue
                else:
                    self.verbose_debug("Attempt number " + str(
                        failed_connections) + " failed. No more attempts to connect will be made.")
                    self.shutdown()
                    self.connected = False
                    return False

    def play(self, messages_count=1):
        """
        send and receive messages to/from server
        :param messages_count: how many messages should be sent from player to server
        """
        for i in range(messages_count):
            try:
                # Send a message:
                message = messages.getgames()
                self.send(message)
                # Receive a response:

                received_data = self.receive()

                sleep(self.timeBetweenMessages)

            except socket.error as e:
                self.verbose_debug("Socket error caught: " + str(e) + ". Shutting down the connection.", True)
                self.socket.close()
                self.connected = False
                return

    def verbose_debug(self, message, important=False):
        """
        if in verbose mode, print out the given message with player index and timestamp
        :param message: message to be printed
        :param important: if not in verbose mode, setting this flag to True will make sure this message gets printed
        """
        if self.verbose or important:
            header = "P" + str(self.index) + " at " + str(datetime.now().time()) + " - "
            print(header, message)

    def shutdown(self):
        self.connected = False
        self.socket.close()
        self.verbose_debug("Closing down the client.", True)

    def send(self, message):
        self.socket.send(message)
        self.last_message = message
        self.verbose_debug("Sent to server: \"" + message + "\".")

    def receive(self):
        received_data = (self.socket.recv(Player.MESSAGE_BUFFER_SIZE)).decode()
        self.verbose_debug("Received from server: \"" + received_data + "\".")
        return received_data


def simulate(number_of_players=1, verbose=True, messages_count=1, time_between_deploys=1):
    """
    deploy client threads/
    :param number_of_players:
    :param verbose: if the clients should operate in verbose mode.
    :param messages_count: how many messages should be sent from player to server
    """
    thread_list = []
    for i in range(number_of_players):
        new_thread = Thread(target=deploy_player, args=(i + 1, verbose, messages_count), daemon=True)
        new_thread.start()
        thread_list.append(new_thread)
        sleep(time_between_deploys)
    return thread_list


def deploy_player(index, verbose=True, messages_count=1):
    p = Player(index, verbose)
    if p.connect():
        p.play(messages_count)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', '--playercount', default=1, help='Number of players to be deployed.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    parser.add_argument('-m', '--messagecount', default=1, help='Number of messages each player should send.')
    args = vars(parser.parse_args())
    simulate(int(args["playercount"]), args["verbose"], int(args["messagecount"]))
