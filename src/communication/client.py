#!/usr/bin/env python
import socket
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from time import sleep
from queue import Queue
from src.communication.info import ClientTypeTag


class Client:
    TIME_BETWEEN_MESSAGES = 5  # time in s between each message sent by client
    INTER_CONNECTION_TIME = 3  # time in s between attemps to connect to server
    CONNECTION_ATTEMPTS = 3  # how many times the clients will retry the attempt to connect
    DEFAULT_HOSTNAME = socket.gethostname()  # keep this as socket.gethostname() if you're debugging on your own pc
    DEFAULT_PORT = 420
    MESSAGE_BUFFER_SIZE = 2048
    MSG_SEPARATOR = ';'

    def __init__(self, index=1, verbose=False):
        """
        constructor.
        :param index: local index used to differentiate between different clients running in threads
        :param verbose: boolean value. if yes, there will be a lot of output printed out.
        """
        self.interConnectionTime = Client.INTER_CONNECTION_TIME
        self.timeBetweenMessages = Client.TIME_BETWEEN_MESSAGES
        self.connectionAttempts = Client.CONNECTION_ATTEMPTS
        self.socket = socket.socket()
        self.index = index
        self.id = None  # will be assigned after connecting to gamemaster.
        self.verbose = verbose
        self.connected = False  # will be changed if connected
        self.last_message = None
        self.typeTag = ClientTypeTag.CLIENT
        self.msg_queue = Queue()
        # self.socket.settimeout(1)

        self.verbose_debug("Client created.")

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
                if self.socket.connect_ex((hostname, port)) == 0:
                    self.connected = True
                    self.verbose_debug("Succesfully connected to server.")
                    return True

                else:
                    raise socket.error

            except socket.error:
                failed_connections += 1
                if failed_connections < self.connectionAttempts:
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

    def talk(self, messages_count=1):
        """
        send and receive messages to/from server
        :param messages_count: how many messages should be sent from client to server
        """
        for i in range(messages_count):
            try:
                '''
                # Send a message:
                message = "Hello."
                self.send(message)
                '''

                # Receive a response:
                received_data = self.receive()
                while len(received_data) < 1:
                    received_data = self.receive()
                self.verbose_debug("Received from server:")
                sleep(self.timeBetweenMessages)

            except socket.error as e:
                self.verbose_debug("Socket error caught: " + str(e) + ". Shutting down the connection.", True)
                self.socket.close()
                self.connected = False
                return

    def verbose_debug(self, message, important=False):
        """
        if in verbose mode, print out the given message with client index and timestamp
        :param message: message to be printed
        :param important: if not in verbose mode, setting this flag to True will make sure this message gets printed
        """
        if self.verbose or important:
            tag = str(self.typeTag.value) + str(self.index)
            header = tag + " at " + str(datetime.now().time()) + " - "
            print(header, message)

    def shutdown(self):
        self.connected = False
        self.socket.close()
        self.verbose_debug("Shutting down the client.", True)
        quit()

    def send(self, message):
        try:
            # We append the MSG_SEPARATOR to the end of each msg
            message += self.MSG_SEPARATOR
            self.socket.send(message.encode())
            sleep(0.01)  # sleep for 1 ms just in case
            self.last_message = message
            self.verbose_debug("Sent to server: \"" + message + "\".")
        except socket.error as e:
            self.verbose_debug("Socket error caught: " + str(e))
            self.shutdown()

    def receive(self) -> str:
        """
        Receives of msg on the socket with a string with messages separated by MSG_SEPARATOR
        Then it adds them to the queue and returns the first unread msg and removes it
        :return: 
        """
        try:
            received_data = (self.socket.recv(Client.MESSAGE_BUFFER_SIZE)).decode()
            if len(received_data) < 1 or received_data is None:
                raise ConnectionAbortedError
            else:
                self.verbose_debug("Received from server: \"" + received_data + "\".")
                for msg in received_data.split(self.MSG_SEPARATOR):
                    if len(msg) > 0:
                        self.msg_queue.put(msg)
                        self.verbose_debug("Added msg to queue: " + msg)
                sleep(0.01)
                return self.msg_queue.get()

        except ConnectionAbortedError:
            self.verbose_debug("Server has shut down. Shutting down the client as well.", True)
            self.shutdown()

        except socket.error as e:
            self.verbose_debug("Socket error caught: " + str(e))
            self.shutdown()


def simulate(number_of_clients=1, verbose=True, messages_count=1, time_between_deploys=1):
    """
    deploy client threads/
    :param number_of_clients:
    :param verbose: if the clients should operate in verbose mode.
    :param messages_count: how many messages should be sent from client to server
    """
    thread_list = []
    for i in range(number_of_clients):
        new_thread = Thread(target=deploy_client, args=(i + 1, verbose, messages_count))
        new_thread.start()
        thread_list.append(new_thread)
        sleep(time_between_deploys)
    return thread_list


def deploy_client(index, verbose=True, messages_count=1):
    c = Client(index, verbose)
    if c.connect():
        c.talk(messages_count)
        c.shutdown()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', '--clientcount', default=1, help='Number of clients to be deployed.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    parser.add_argument('-m', '--messagecount', default=1, help='Number of messages each client should send.')
    args = vars(parser.parse_args())
    simulate(int(args["clientcount"]), args["verbose"], int(args["messagecount"]))
