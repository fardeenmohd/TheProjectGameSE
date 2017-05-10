#!/usr/bin/env python
from threading import Thread
from time import sleep
from unittest import TestCase

from src.communication import server, client, player, gamemaster


class TestIntegration(TestCase):
    def setUp(self):

        self.mock_player = player.Player(1, verbose=True)
        self.mock_server = server.CommunicationServer(verbose=True)
        self.mock_gamemaster = gamemaster.GameMaster(verbose=True)

        listening_server_thread = Thread(target=self.mock_server.listen, daemon=True)
        listening_server_thread.start()

    def tearDown(self):
        self.mock_player.shutdown()
        self.mock_gamemaster.shutdown()
        self.mock_server.shutdown()

        del self.mock_server
        del self.mock_gamemaster
        del self.mock_player