#!/usr/bin/env python
import pytest
import socket
import threading
import time

from src.communication import player


class TestPlayer:
    def run_mock_server(self, test):
        test.bind((player.Player.DEFAULT_HOSTNAME, player.Player.DEFAULT_PORT))
        test.listen()
        test.accept()

    def test_connect_to_the_server(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        time.sleep(1)
        assert test_player.connected is True
        self.close_testing_environment(test_player, mock_server)

    def test_id_received(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        time.sleep(1)
        assert test_player.id is ''
        self.close_testing_environment(test_player, mock_server)

    def test_disconnect_to_the_server(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        test_player.shutdown()
        assert test_player.connected is False
        mock_server.close()

    def test_send_to_server(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        time.sleep(1)
        test_player.play()
        time.sleep(1)
        received = mock_server.recv(test_player.MESSAGE_BUFFER_SIZE)

        assert received is not None

    def initialize_testing_environment(self):
        test_player = player.Player(0, verbose=True)
        mock_server = socket.socket()
        server_thread = threading.Thread(target=self.run_mock_server, daemon=True, args=(mock_server,))
        server_thread.start()
        return test_player, mock_server

    def close_testing_environment(self, test_player, mock_server):
        test_player.shutdown()
        mock_server.close()
