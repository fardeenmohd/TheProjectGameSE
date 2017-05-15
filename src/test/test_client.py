#!/usr/bin/env python
import socket
import threading
import time
from unittest import TestCase

from src.communication import client


class TestClient(TestCase):
    def setUp(self):
        self.mock_client = client.Client(1, verbose=True)
        self.mock_server = socket.socket()

        self.server_thread = threading.Thread(target=self.run_mock_server, daemon=True)
        self.server_thread.start()

    def run_mock_server(self):
        self.mock_server.bind((client.Client.DEFAULT_HOSTNAME, client.Client.DEFAULT_PORT))
        self.mock_server.listen()
        sock, addr = self.mock_server.accept()
        sock.send('1'.encode())

    def tearDown(self):
        self.mock_client.shutdown()
        self.mock_server.close()

    def test_connect_to_the_server(self):
        self.mock_client.connect()
        time.sleep(1)

        assert self.mock_client.connected is True

    def test_disconnect_to_the_server(self):
        self.mock_client.connect()
        self.mock_client.shutdown()

        assert self.mock_client.connected is False

    def test_received(self):
        self.mock_client.connect()
        time.sleep(1)

    def test_send_message_to_server(self):
        self.mock_client.connect()
        self.mock_client.send("Hello.")

        assert self.mock_client.last_message is not None
