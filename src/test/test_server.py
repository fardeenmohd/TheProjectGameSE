#!/usr/bin/env python

import os
import socket
from threading import Thread
from time import sleep
from unittest import TestCase

from src.communication import messages
from src.communication import server
from src.communication.unexpected import GameConnectionError

print(os.getcwd())
os.chdir("../../src/communication/")


class TestServer(TestCase):
    def setUp(self):
        self.mock_server = server.CommunicationServer(True)
        self.listening_thread = Thread(target=self.mock_server.listen, daemon=True)
        print()

    def tearDown(self):
        """
         Shuts the self.mock clients and server down
        """
        self.mock_server.shutdown()

    def test_listening(self):
        """
        test if new client connections are being accepted.
        """
        print("Listening test.")

        self.listening_thread.start()
        num_of_clients = 5

        for i in range(num_of_clients):
            new_thread = Thread(target=self.connect_client_to_server, daemon=True)
            new_thread.start()
            # give the clients some time to actually connect:
            sleep(0.01)

        assert len(self.mock_server.clients) == num_of_clients

    def connect_client_to_server(self, client=None):
        """
        Mock client connects to the server
        """
        if client is None:
            client = socket.socket()
        if client.connect_ex((self.mock_server.hostname, self.mock_server.port)) == 0:
            pass
        else:
            raise GameConnectionError("Failed to connect to server.")
        # sleep for a second so that the client remains connected for some time
        sleep(1)
        return client

    def test_send(self):
        print("Test the send function.")

        self.listening_thread.start()

        mock_client = self.connect_client_to_server()
        self.mock_server.send(self.mock_server.clients["0"], "hello")

        received = mock_client.recv(1024).decode()
        assert received == "hello⌁"

    def test_relay_msg_to_player(self):
        # in fact a special type of send.

        print("Test the relay function.")
        self.listening_thread.start()

        mock_client = self.connect_client_to_server()
        message = messages.Data("0", False)  # any type of message with playerId, really

        self.mock_server.relay_msg_to_player(message)
        received = mock_client.recv(1024).decode()
        assert received == message + "⌁"

    def test_receive(self):
        print("Test the receive function.")
        self.listening_thread.start()

        mock_client = socket.socket()

        Thread(target=self.connect_client_to_server, args=[mock_client], daemon=True)

        mock_client.send("hello.".encode())
        received = self.mock_server.receive(self.mock_server.clients["0"])
        mock_client.close()
        assert received == "hello."
