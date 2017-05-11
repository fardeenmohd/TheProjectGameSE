#!/usr/bin/env python
from threading import Thread
from time import sleep
from unittest import TestCase

from src.communication import server, client, player, gamemaster, messages


class TestIntegration(TestCase):
    def setUp(self):
        self.mock_player1 = player.Player(1, verbose=True)
        self.mock_player2 = player.Player(2, verbose=True)
        self.mock_server = server.CommunicationServer(verbose=True)
        self.mock_gamemaster = gamemaster.GameMaster(verbose=True)

        self.listening_server_thread = Thread(target=self.mock_server.listen, daemon=True)
        self.listening_server_thread.start()

    def setup_legit_gm(self):
        self.mock_gamemaster.connect()

    def tearDown(self):

        self.mock_server.running = False
        self.mock_player1.shutdown()
        self.mock_player2.shutdown()
        self.mock_gamemaster.shutdown()
        self.mock_server.shutdown()

    def register_game(self):
        self.mock_gamemaster.connect()
        self.mock_gamemaster.send(messages.RegisterGame('easy clone', 1, 1))

        received = self.mock_gamemaster.receive()

        if received is not None:
            self.mock_gamemaster.handle_confirm_registration(received)

    def test_game_registration(self):
        self.register_game()
        assert self.mock_gamemaster.info.id != "-1"





