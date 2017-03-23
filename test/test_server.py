#!/usr/bin/env python
import sys, socket, threading, time
from src.communication import server
from multiprocessing import Process
# from unittest.mock import MagicMock,patch,Mock TODO maybe use this library for testing


class TestServer:

    def run_server_to_be_tested(self, test):
        test.listen()

    def test_client_count(self):
        mock_client, test_server = self.initialize_testing_environment()
        assert test_server.clientCount == 1
        self.close_testing_environment(mock_client, test_server)

    def test_player_id(self):
        mock_client, test_server = self.initialize_testing_environment()
        received = mock_client.recv(test_server.DEFAULT_BUFFER_SIZE)
        assert received.decode() == '0'
        self.close_testing_environment(mock_client, test_server)

    def initialize_testing_environment(self):
        """
        Creates a server that will be tested, as well as a single mock client that will connect to it. Returns both
        :return:
        """
        test_server = server.CommunicationServer(verbose=True, host=server.CommunicationServer.DEFAULT_HOSTNAME,
                                                 port=server.CommunicationServer.DEFAULT_PORT)
        server_thread = threading.Thread(target=self.run_server_to_be_tested, daemon=True, args=(test_server,))
        server_thread.start()
        mock_client = socket.socket()
        mock_client.connect((server.CommunicationServer.DEFAULT_HOSTNAME, server.CommunicationServer.DEFAULT_PORT))
        time.sleep(0.1)
        return mock_client, test_server

    def close_testing_environment(self, mock_client, test_server):
        """
         Shuts the mock client and server down
        """
        mock_client.close()
        test_server.shutdown()


tester = TestServer()
tester.test_client_count()
tester.test_player_id()
