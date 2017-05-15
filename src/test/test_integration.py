#!/usr/bin/env python
from threading import Thread
from time import sleep
from unittest import TestCase

from src.communication import server, gamemaster, messages
from src.communication.player import Player


class TestIntegration(TestCase):
    def setUp(self):
        self.mock_server = server.CommunicationServer(verbose=True)
        self.mock_gamemaster = gamemaster.GameMaster(verbose=True)
        self.mock_player1 = Player(1, True, "easy clone")
        self.mock_player2 = Player(2, True, "easy clone")

        self.listening_server_thread = Thread(target=self.mock_server.listen, daemon=True)
        self.listening_server_thread.start()
        print()

    def tearDown(self):
        sleep(1)
        self.mock_gamemaster.shutdown()
        self.mock_server.shutdown()
        self.mock_player1.shutdown()
        self.mock_player2.shutdown()

    def register_game(self):
        self.mock_gamemaster.connect()
        self.mock_gamemaster.send(messages.RegisterGame('easy clone', 1, 1))

        received = self.mock_gamemaster.receive()

        if received is not None:
            self.mock_gamemaster.handle_confirm_registration(received)

    def setup_legit_gm(self):
        if self.mock_gamemaster.connect():
            self.register_game()

    def setup_players(self):
        if self.mock_player1.connect():
            Thread(target=self.player_join, args=[self.mock_player1]).start()
        if self.mock_player2.connect():
            Thread(target=self.player_join, args=[self.mock_player2]).start()

    def player_join(self, player: Player):
        if player.try_join():
            player.play()

    def test_players_connecting(self):
        print("Test connecting two Players to server.")
        self.setup_players()
        assert len(self.mock_server.clients) == 2

    def test_game_registration(self):
        print("Test game registration.")
        self.register_game()
        # if info is not -1, then it means we succesfully registered (and received game id):
        assert self.mock_gamemaster.info.id != "-1"

    def test_players_joining(self):
        print("Test two Players joining a game.")
        self.register_game()
        Thread(target=self.mock_gamemaster.wait_for_players).start()
        self.setup_players()
        sleep(1)  # sleep for a second to let the players connect
        assert self.mock_gamemaster.get_num_of_players == 2

    def test_game_ends(self):
        print("Test whether a game will end within 1500 seconds.")
        self.register_game()
        Thread(target=self.mock_gamemaster.wait_for_players).start()
        self.setup_players()
        i = 0
        while i < 1500:
            if self.mock_gamemaster.info.finished:
                assert True
                return
            sleep(1)
            i += 1
        assert False
