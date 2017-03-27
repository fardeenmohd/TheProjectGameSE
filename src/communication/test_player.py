#!/usr/bin/env python
import socket
import threading
import time
from unittest import TestCase

from communication import player


class TestPlayer(TestCase):
	def setUp(self):
		self.mock_player = player.Player(1, verbose = True)
		self.mock_server = socket.socket()

		self.server_thread = threading.Thread(target = self.run_mock_server, daemon = True)
		self.server_thread.start()

	def run_mock_server(self):
		self.mock_server.bind((player.Player.DEFAULT_HOSTNAME, player.Player.DEFAULT_PORT))
		self.mock_server.listen()
		client, addr = self.mock_server.accept()

	def tearDown(self):
		self.mock_player.shutdown()
		self.mock_server.close()

	def test_connect_to_the_server(self):
		self.mock_player.connect()
		time.sleep(1)

		assert self.mock_player.connected is True

	def test_disconnect_to_the_server(self):
		self.mock_player.connect()
		self.mock_player.shutdown()

		assert self.mock_player.connected is False

	def test_received(self):
		self.mock_player.connect()
		time.sleep(1)

	def test_send_message_to_server(self):
		self.mock_player.connect()
		time.sleep(1)
		self.mock_player.play()
		time.sleep(1)
		self.mock_player.play()

		assert self.mock_player.last_message is not None

	def test_failed_connection_attempts_to_a_closed_server(self):
		self.mock_server.close()
		connection_status = self.mock_player.connect()

		assert connection_status is False
