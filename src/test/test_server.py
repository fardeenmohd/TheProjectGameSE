#!/usr/bin/env python

import os
from threading import Thread
from time import sleep
from unittest import TestCase
print(os.getcwd())
os.chdir("src/communication")
from src.communication.info import ClientInfo
from src.communication.player import Player
from src.communication.gamemaster import GameMaster
from src.communication import server
from src.communication import messages
#os.chdir("../../test")
# from unittest.self.mock import Magicself.mock,patch,self.mock TODO maybe use this library for testing


class TestServer(TestCase):
    def setUp(self):
        self.testing_server = server.CommunicationServer(True)

    def test_listening(self):
        """
        test if new client connections are being accepted.
        """
        print("Client count test.")

        listening_thread = Thread(target=self.testing_server.listen, daemon=True)
        listening_thread.start()
        num_of_clients = 5

        for i in range(num_of_clients):
            new_thread = Thread(target=self.connect_player_to_server, daemon=True)
            new_thread.start()
            # give the clients some time to actually connect:
            sleep(0.01)

        assert self.testing_server.client_indexer == num_of_clients

    def connect_player_to_server(self):
        """
        Mock player connects to the server
        :return:
        """
        p = Player(verbose=True)
        if p.connect():
            pass

    def test_send(self):
        print("Testing the send function.")

        listening_thread = Thread(target=self.testing_server.listen, daemon=True)
        listening_thread.start()
        mock_gm = GameMaster(verbose=True)
        mock_gm.connect()
        while len(self.testing_server.clients) == 0:
            sleep(0.001)
        print(str(self.testing_server.clients))
        self.testing_server.send(self.testing_server.clients['0'], "hello")  # he should be the first client
        received = mock_gm.receive()
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
        listening_thread = Thread(target=self.testing_server.listen, daemon=True)
        listening_thread.start()

        self.testing_server.clientLimit = 5
        num_of_clients = 5

        for i in range(num_of_clients):
            new_thread = Thread(target=self.connect_player_to_server, daemon=True)
            new_thread.start()
            # give the clients some time to actually connect:
            sleep(0.01)

        mock_player = Player()
        mock_player.connect()

        assert self.testing_server.client_indexer == self.testing_server.clientLimit

    def test_try_register_game(self):
        listening_thread = Thread(target=self.testing_server.listen, daemon=True)
        listening_thread.start()
        gm = GameMaster()
        gm.connect()
        gm_thread = Thread(target=gm.run, daemon=True)
        gm_thread.start()
        sleep(1)  # add some time for some communication to happen between sever and gm
        # we test games_indexer because only the try_register_game function increments it
        assert self.testing_server.games_indexer == 1

    def test_relay_msg_to_player(self):
        listening_thread = Thread(target=self.testing_server.listen, daemon=True)
        listening_thread.start()
        gm = GameMaster()
        gm.connect()
        gm_thread = Thread(target=gm.run, daemon=True)
        gm_thread.start()
        sleep(1)  # add some time for some communication to happen between sever and gm
        # we test games_indexer because only the try_register_game function increments it
        mock_player = Player()
        mock_player.connect()
        test_msg = messages.Data(1, game_finished=False)  # mock_player should be at index 1 since GM is at index 0
        self.testing_server.relay_msg_to_player(test_msg)
        received = mock_player.receive()
        assert received == test_msg

    def test_split_that_message(self):
        listening_thread = Thread(target=self.testing_server.listen, daemon=True)
        listening_thread.start()
        num_of_split_msgs = 5
        test_msg = ""
        for i in range(num_of_split_msgs):
            test_msg += (messages.Data(0, game_finished=False) + self.testing_server.MSG_SEPARATOR)
        assert self.testing_server.split_that_message(test_msg, ClientInfo()) == num_of_split_msgs

    def tearDown(self):
        """
         Shuts the self.mock clients and server down
        """
        self.testing_server.shutdown()
