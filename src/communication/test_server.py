#!/usr/bin/env python
import socket
from threading import Thread
from time import sleep
from unittest import TestCase

from src.communication import server, messages


# from unittest.self.mock import Magicself.mock,patch,self.mock TODO maybe use this library for testing


class TestServer(TestCase):
    def setUp(self):
        self.mock_server = server.CommunicationServer(True)

    def test_listening(self):
        """
        test if new client connections are being accepted.
        """
        print("Client count test.")

        listening_thread = Thread(target=self.mock_server.listen, daemon=True)
        listening_thread.start()
        num_of_clients = 5

        for i in range(num_of_clients):
            new_thread = Thread(target=self.connect_to_server, daemon=True)
            new_thread.start()
            # give the clients some time to actually connect:
            sleep(0.01)

        assert self.mock_server.client_indexer == num_of_clients

    def connect_to_server(self):
        mock_client = socket.socket()
        mock_client.connect((self.mock_server.host, self.mock_server.port))
        while True:
            sleep(1)

    def test_send(self):
        print("Test the send function.")

        listening_thread = Thread(target=self.mock_server.listen, daemon=True)
        listening_thread.start()

        mock_client = socket.socket()
        mock_client.connect((self.mock_server.host, self.mock_server.port))


        received = mock_client.recv(1024).decode()
        assert received == "hello"

    # def test_receive(self):
    #     print("Test the receive function.")
    #
    #     self.mock_server.socket.listen()
    #
    #     mock_client = socket.socket()
    #     mock_client.connect((self.mock_server.host, self.mock_server.port))
    #
    #     client_sock, addr = self.mock_server.socket.accept()
    #
    #     mock_client.send("hello.".encode())
    #     print(self.mock_server.clients)
    #     received = self.mock_server.receive(self.mock_server.clients["1"].value)
    #
    #     assert received == "hello."

    def test_client_limit(self):
        """
        We create DEFAULT_CLIENT_LIMIT amount of clients then we try to connect another mock_client
        This extra mock_client should not be able to connect so we test that there is still no more than
        DEFAULT_CLIENT_LIMIT amount of clients on the server
        :return:
        """
        listening_thread = Thread(target=self.mock_server.listen, daemon=True)
        listening_thread.start()

        self.mock_server.clientLimit = 5
        num_of_clients = 5

        for i in range(num_of_clients):
            new_thread = Thread(target=self.connect_to_server, daemon=True)
            new_thread.start()
            # give the clients some time to actually connect:
            sleep(0.01)

        mock_client = socket.socket()
        mock_client.connect((self.mock_server.host, self.mock_server.port))

        assert self.mock_server.client_indexer == self.mock_server.clientLimit

    def tearDown(self):
        """
         Shuts the self.mock clients and server down
        """
        self.mock_server.shutdown()
