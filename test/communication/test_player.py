#!/usr/bin/env python
import pytest
import socket
from threading import Thread

from src.communication import player


class TestPlayer:
    DEFAULT_HOSTNAME = socket.gethostname()
    DEFAULT_PORT = 420
    DEFAULT_BUFFER_SIZE = 1024

    def run_fake_server(self):
        server_sock = socket.socket()
        server_sock.bind((self.DEFAULT_HOSTNAME, self.DEFAULT_PORT))
        server_sock.listen(0)
        server_sock.accept()
        server_sock.close()

    def test_connect_and_disconnect(self):
        server_thread = Thread(target=self.run_fake_server())
        server_thread.start()

        guinea_player = player

        assert guinea_player.run(1, False, 1)
