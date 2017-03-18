#!/usr/bin/env python
import socket
import time
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread


class Player:
	TIME_BETWEEN_MESSAGES = 5  # time in s between each message sent by player
	INTER_CONNECTION_TIME = 10  # time in s between attemps to connect to server
	CONNECTION_ATTEMPTS = 3  # how many times the clients will retry the attempt to connect
	DEFAULT_HOSTNAME = socket.gethostname()  # keep this as socket.gethostname() if you're debugging on your own pc
	DEFAULT_PORT = 4000
	MESSAGE_BUFFER_SIZE = 1024

	def __init__(self, index, verbose):
		"""
		constructor.
		:param index: local index used to differentiate between different players running in threads
		:param verbose: boolean value. if yes, there will be a lot of output printed out.
		"""
		self.socket = socket.socket()
		self.index = index
		self.id = None  # will be assigned after connecting to server.
		self.verbose = verbose
		self.verbose_debug("Player created.")

	def connect(self, hostname = DEFAULT_HOSTNAME, port = DEFAULT_PORT):
		"""
		try to connect to server and receive UID
		:param hostname: host name to connect to
		:param port: port to connect to
		"""

		failed_connections = 0

		while True:
			try:
				self.verbose_debug("Trying to connect to server...")
				self.socket.connect((hostname, port))
				self.verbose_debug("Connected to server.")

				received = self.socket.recv(Player.MESSAGE_BUFFER_SIZE)
				self.id = received.decode()
				self.verbose_debug("Received UID from server=" + str(self.id))
				return

			except socket.error:
				if failed_connections < Player.CONNECTION_ATTEMPTS:
					failed_connections += 1
					self.verbose_debug("Attempt number " + str(failed_connections) + " failed. Trying again in " + str(
						Player.INTER_CONNECTION_TIME) + " seconds.")
					time.sleep(Player.INTER_CONNECTION_TIME)
					continue
				else:
					self.verbose_debug("Attempt number " + str(
						failed_connections) + " failed. No more attempts to connect will be made.")
					return

	def play(self, messages_count = 1):
		"""
		send and receive messages to/from server
		:param messages_count: how many messages should be sent from player to server
		"""
		for i in range(messages_count):
			try:
				# Send a message:
				message = "Hello server."  # TODO: use a randomly-taken XML message instead
				self.socket.send(message.encode())
				self.verbose_debug("Sent to server:" + message)

				# Receive a response:
				received_data = self.socket.recv(Player.MESSAGE_BUFFER_SIZE)
				self.verbose_debug("Received from server:" + received_data.decode())
				time.sleep(Player.TIME_BETWEEN_MESSAGES)

			# below is legacy code from when messages used to be typed in from console
			# if message == "close":
			# 	self.socket.close()
			# 	self.verbose_debug("Received a message from server: \"" + received_data.decode()) + "\""
			# 	self.verbose_debug("Disconnected.")

			except ConnectionAbortedError:
				self.verbose_debug("Disconnected by server (or by some other issue). Shutting down.")
				self.socket.close()
				return

	def verbose_debug(self, message):
		"""
		if in verbose mode, print out the given message with player index and timestamp
		:param message: message to be print
		"""
		if (self.verbose):
			header = "P" + str(self.index) + " at " + str(datetime.now().time()) + " - "
			print(header, message)


def run(number_of_players = 1, verbose = True, messages_count = 1):
	"""
	deploy client threads/
	:param verbose: if the clients should operate in verbose mode.
    :param messages_count: how many messages should be sent from player to server
	"""
	for i in range(number_of_players):
		Thread(target = deploy_player, args = (i + 1, verbose, messages_count)).start()


def deploy_player(index, verbose = True, messages_count = 1):
	p = Player(index, verbose)
	p.connect()
	p.play(messages_count)


parser = ArgumentParser()
parser.add_argument('-c', '--playercount', default = 1, help = 'Number of players to be deployed.')
parser.add_argument('-v', '--verbose', action = 'store_true', default = True, help = 'Use verbose debugging mode.')
parser.add_argument('-m', '--messagecount', default = 1, help = 'Number of messages each player should send.')
args = vars(parser.parse_args())

run(args["playercount"], args["verbose"], args["messagecount"])
