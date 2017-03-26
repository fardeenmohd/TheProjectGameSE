#!/usr/bin/env python
import sys, socket, threading, time
from src.communication import server
from multiprocessing import Process
# from unittest.mock import MagicMock,patch,Mock TODO maybe use this library for testing


class TestServer:

    def run_server_to_be_tested(self, test):
        test.listen()

    def test_client_count(self):
        mock_clients, test_server = self.initialize_testing_environment()
        assert test_server.clientCount == 1
        self.close_testing_environment(mock_clients, test_server)

    def test_player_id(self):
        mock_clients, test_server = self.initialize_testing_environment()
        received = mock_clients[0].recv(test_server.DEFAULT_BUFFER_SIZE)
        assert received.decode() == '0'
        self.close_testing_environment(mock_clients, test_server)

    def test_client_limit(self):
        """
        We create DEFAULT_CLIENT_LIMIT amount of clients then we try to connect another client
        This extra client should not be able to connect so we test that there is still no more than
        DEFAULT_CLIENT_LIMIT amount of clients on the server
        :return:
        """
        mock_clients, test_server = self.initialize_testing_environment(server.CommunicationServer.DEFAULT_CLIENT_LIMIT)
        extra_mock_client = socket.socket()
        extra_mock_client.connect((server.CommunicationServer.DEFAULT_HOSTNAME,
                                   server.CommunicationServer.DEFAULT_PORT))
        time.sleep(0.01)
        print("Num of mock_clients: " + str(len(mock_clients)))

        assert test_server.clientCount == test_server.DEFAULT_CLIENT_LIMIT
        self.close_testing_environment(mock_clients, test_server)

    def initialize_testing_environment(self, num_of_clients=1):
        """
        Creates a server that will be tested, as well as a single mock client that will connect to it. Returns both
        :return:
        """
        mock_clients = []
        test_server = server.CommunicationServer(verbose=True, host=server.CommunicationServer.DEFAULT_HOSTNAME,
                                                 port=server.CommunicationServer.DEFAULT_PORT)
        server_thread = threading.Thread(target=self.run_server_to_be_tested, daemon=True, args=(test_server,))
        server_thread.start()
        for i in range(num_of_clients):
            connected = False
            mock_client = socket.socket()
            while not connected:
                try:
                    mock_client.connect((server.CommunicationServer.DEFAULT_HOSTNAME,
                                         server.CommunicationServer.DEFAULT_PORT))
                    connected = True
                except Exception as e:
                    pass  # Do nothing, just try again

            mock_clients.append(mock_client)
            time.sleep(0.01)  # sleep in order to allow client to properly connect

        while test_server.clientCount is not num_of_clients:
            time.sleep(0.001)  # we give the server some time for the mock clients to connect

        return mock_clients, test_server

    def close_testing_environment(self, mock_clients, test_server):
        """
         Shuts the mock clients and server down
        """
        for mock_client in mock_clients:
            mock_client.close()
        test_server.shutdown()


ts = TestServer()
ts.test_client_count()
