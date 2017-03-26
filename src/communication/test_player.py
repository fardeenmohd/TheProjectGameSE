#!/usr/bin/env python
import pytest
import socket
import threading
import time

from src.communication import player


class TestPlayer:
    def test_connect_to_the_server(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        time.sleep(1)

        assert test_player.connected is True
        self.close_testing_environment(test_player, mock_server)

    def test_disconnect_to_the_server(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        test_player.shutdown()

        assert test_player.connected is False
        mock_server.close()

    def test_id_received(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        time.sleep(1)

        assert test_player.id is "1"
        self.close_testing_environment(test_player, mock_server)

    def test_send_message_to_server(self):
        test_player, mock_server = self.initialize_testing_environment()
        test_player.connect()
        time.sleep(1)
        test_player.play()
        time.sleep(1)
        test_player.play()

        assert test_player.last_message is not None
        self.close_testing_environment(test_player, mock_server)

    def test_failed_connection_attempts_to_a_closed_server(self):
        test_player, mock_server = self.initialize_testing_environment(False)
        connection_status = test_player.connect()

        assert connection_status is False
        self.close_testing_environment(test_player, mock_server)

    def initialize_testing_environment(self, run_server=True):
        test_player = player.Player(1, verbose=True)
        mock_server = socket.socket()

        if run_server is True:
            server_thread = threading.Thread(target=self.run_mock_server, daemon=True, args=(mock_server,))
            server_thread.start()

        return test_player, mock_server

    @staticmethod
    def run_mock_server(test):
        test.bind((player.Player.DEFAULT_HOSTNAME, player.Player.DEFAULT_PORT))
        test.listen()
        client, addr = test.accept()
        client.send("1".encode())

    @staticmethod
    def close_testing_environment(test_player, mock_server):
        test_player.shutdown()
        mock_server.close()
