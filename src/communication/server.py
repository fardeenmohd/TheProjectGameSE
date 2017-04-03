#!/usr/bin/python
import socket
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from enum import Enum, auto
from threading import Thread
from time import sleep

from src.communication import messages
from src.communication.client import ClientTypeTag
from src.communication.info import ClientInfo, GameInfo

XML_MESSAGE_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"
ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")


class Communication(Enum):
    """
    an Enum class for flags which will be useful later on for distinguishing between message recipients
    """
    SERVER_TO_CLIENT = auto()
    CLIENT_TO_SERVER = auto()
    OTHER = auto()


class CommunicationServer:
    # some constants:
    INTER_PRINT_STATE_TIME = 5
    DEFAULT_BUFFER_SIZE = 1024
    DEFAULT_PORT = 420
    DEFAULT_TIMEOUT = 10
    DEFAULT_CLIENT_LIMIT = 10
    DEFAULT_HOSTNAME = socket.gethostname()

    def __init__(self, verbose, host = DEFAULT_HOSTNAME, port = DEFAULT_PORT, client_limit = DEFAULT_CLIENT_LIMIT):
        """
        constructor.
        :param verbose:
        :param host:
        :param port:
        """

        # declare fields:
        self.running = True
        self.host = host
        self.port = port
        self.clientLimit = client_limit
        self.verbose = verbose

        self.socket = socket.socket()
        self.clients = {}  # client_id => ClientInfo object
        self.games = {}  # game_id => GameInfo object
        self.client_indexer = 0
        self.games_indexer = 0

        try:
            self.socket.bind((host, port))

        except OSError as e:
            self.verbose_debug("Error while setting up the socket: " + str(e), True)
            raise e

        self.verbose_debug("Created server with hostname: " + host + " on port " + str(port), True)

    def verbose_debug(self, message, important = False):
        """
        if in verbose mode, print out the given message with a timestamp
        :param message: message to be printed
        :param important: if not in verbose mode, setting this flag to True will make sure this message gets printed
        """
        if self.verbose or important:
            header = "S at " + str(datetime.now().time()) + " -"
            print(header, message)

    def print_state(self):
        """
        method running on a separate Thread, prints the current state of the server every couple of seconds
        time between each printing of debug messages is specified by the constant CommunicationServer.INTER_PRINT_STATE_TIME
        """
        while self.running:
            self.verbose_debug("Currently there are " + str(len(self.clients)) + " clients connected.")
            sleep(CommunicationServer.INTER_PRINT_STATE_TIME)

    def listen(self):
        """
        accept client connections and deploy threads.
        """
        self.socket.listen()
        self.verbose_debug("Started listening")

        Thread(target = self.print_state, daemon = True).start()
        Thread(target = self.accept_clients, daemon = True).start()

        # wait for and respond to user commands:
        try:
            while self.running:
                command = input()

                if command == "stop" or command == "close" or command == "quit" or command == "exit":
                    raise KeyboardInterrupt

                elif command == "state":
                    self.verbose_debug("Currently there are " + str(len(self.clients)) + " clients connected.", True)

                elif command == "clients":
                    self.verbose_debug("Currently connected clients:", True)
                    if len(self.clients) > 0:
                        for client in self.clients:
                            print(" " + client.get_tag() + ": " + str(client.socket.getsockname()))
                    else:
                        print(" There are no currently connected clients.")

                elif command == "toggle-verbose":
                    self.verbose = not self.verbose

                elif str(command).startswith("echo "):
                    command = str(command)
                    message_text = command.split(" ")
                    speech = ""
                    for word in message_text:
                        if word != "echo":
                            speech += word + " "
                    print(speech)

        except KeyboardInterrupt:
            # handle C-C and "stop" commands
            self.verbose_debug("Server closed by user.", True)
            self.shutdown()

    def accept_clients(self):
        """
        method running endlessly on a separate thread, accepts new clients and deploys threads to handle them
        """
        while self.running:
            # block and wait until a client connects:
            client_socket, address = self.socket.accept()

            if len(self.clients) < self.clientLimit:
                # if client limit not exceeded, handle the new client:
                # send a single byte which says "greetings"
                self.verbose_debug("Accepted some client, sending greeting byte...")
                client_socket.send('1'.encode())
                self.register_connection(client_socket, self.client_indexer)
                self.client_indexer += 1
            else:
                # if client limit exceeded, send a "sorry, server full" byte:
                client_socket.send('0'.encode())
                client_socket.close()
                sleep(1)

    def register_connection(self, client_socket, client_id):
        new_client = ClientInfo(client_id, socket = client_socket)
        self.clients[client_id] = new_client

        self.verbose_debug(
            "New client: " + new_client.get_tag() + " with address " + str(client_socket.getsockname()) + " connected.")
        if len(self.clients) == self.clientLimit:
            self.verbose_debug("Client capacity reached.")

        Thread(target = self.handle_client, args = [new_client], daemon = True).start()

    def handle_client(self, new_client):
        """
        Receive and send messages to/from a given client.
        :type new_client: ClientInfo
        :param new_client: ClientInfo object about the new client
        """

        try:
            if self.running:
                # read the first message:
                received_data = self.receive(new_client)

                if "RegisterGame" in received_data:
                    new_client.type = ClientTypeTag.GAME_MASTER
                elif "GetGames" in received_data:
                    new_client.type = ClientTypeTag.PLAYER

                if new_client.type == ClientTypeTag.CLIENT:
                    self.verbose_debug("Unknown client connected to server, disconnecting him: ", True)
                    self.disconnect_client(new_client.id)

                if new_client.type == ClientTypeTag.PLAYER:
                    self.verbose_debug("Identified C" + str(new_client.id) + " as a player")
                    self.handle_player(new_client)

                elif new_client.type == ClientTypeTag.GAME_MASTER:
                    self.verbose_debug("Identified " + new_client.get_tag() + " as a Game Master")
                    self.handle_gm(new_client, received_data)

        except ConnectionAbortedError:
            self.verbose_debug(new_client.get_tag() + " disconnected. Closing connection.", True)
            self.disconnect_client(new_client.id)

        except socket.error as e:
            self.verbose_debug("Closing connection with " + new_client.get_tag() + " due to a socket error: " + str(e), True)
            self.disconnect_client(new_client.id)

        except Exception as e:
            self.verbose_debug("Disconnecting " + new_client.get_tag() + " due to an unexpected exception: " + str(e) + ".", True)
            self.disconnect_client(new_client.id)
            raise e

    def handle_player(self, player):
        # first_message was a GetGames xml
        self.send(player, messages.registered_games(self.games))

        while self.running:
            received = self.receive(player)

            # parse the message, relay it to GM

            if "JoinGame" in received:
                join_game_root = ET.fromstring(received)

                # check if game with this name exists:
                game_name = join_game_root.attrib["gameName"]

                for game_index, game_info in self.games.items():
                    if game_info.name == game_name:
                        # game found, so we will update JoinGame with player_id and send it to GM:
                        join_game_root.attrib["playerId"] = str(player.id)
                        message = ET.tostring(join_game_root, encoding = 'unicode', method = 'xml')

                        # find the right GM:
                        for client_index, client in self.clients.items():
                            if client.type == ClientTypeTag.GAME_MASTER and client.game_name == game_name:
                                self.send(client, message)

                    else:
                        # no game with this name, send rejection
                        self.send(player, messages.reject_joining_game(game_name, player.id))

            elif "KnowledgeExchangeRequest" in received or "Data" in received:
                # TODO: parse the message and send it to the correct player (NOT THE GAME MASTER)
                pass

            else:
                # TODO: otherwise, the message is a regular message and as such should be simply relayed to the correct GM
                pass

    def handle_gm(self, gm, first_message):
        # first_message should be a RegisterGames xml

        # Parse first register games msg
        register_games_root = ET.fromstring(first_message)
        new_blue_players = 0
        new_red_players = 0
        new_game_name = ""

        for register_game in register_games_root.findall(XML_MESSAGE_TAG + "NewGameInfo"):
            new_game_name = register_game.get("gameName")
            new_blue_players = int(register_game.get("blueTeamPlayers"))
            new_red_players = int(register_game.get("redTeamPlayers"))
        # done parsing.

        # check if game with this name exists:
        if len([game for game_index, game in self.games.items() if game.name == new_game_name]) > 0:
            # reject the registration.
            self.verbose_debug(
                gm.get_tag() + " tried to register a game with name: \"" + new_game_name + "\". Rejecting, because there "
                                                                                           "already is a game with this "
                                                                                           "name.")
            self.send(gm, messages.reject_game_registration())

            # GM will be trying again, so let's wait for his second attempt:
            self.receive(gm)

        else:
            # create the new game:
            self.games[self.games_indexer] = GameInfo(id = self.games_indexer, name = new_game_name, open = True)
            gm.game_name = new_game_name
            self.verbose_debug(
                gm.get_tag() + " registered a new game, with name: " + new_game_name + " num of blue players: " + str(
                    new_blue_players) + " num of red players: " + str(new_red_players))
            self.send(gm, messages.confirm_game_registration(self.games_indexer))
            self.games_indexer += 1

            # after registering the game, GM will be receiving JoinGame messages from players.
            # then, he will send us a GameStarted message
            # TODO: parse a GameStarted message

            # TODO: relay other messages to players etc.

    def wait_for_message(self, message_name, client, max_attempts = 10):
        """
        This method blocks until it receives a certain message, it will try max_attempts amount of times to receive it
        Then it returns the full message when it is received
        :param message_name:
        :param client:
        :param max_attempts:
        :return:
        """
        received_data = self.receive(client)
        attempts = 1
        while message_name not in received_data and self.running and attempts <= max_attempts:
            received_data = self.receive(client)
            attempts += 1
        return received_data

    def send(self, recipient, message):
        """
        a truly vital method. Sends a given message to a recipient.
        :type recipient: ClientInfo
        :param recipient: socket object of the recipient.
        :param message: message to be passed, any type. will be encoded as string.
        """
        message = str(message)
        recipient.socket.send(message.encode())
        self.verbose_debug("Message sent to " + recipient.get_tag() + ": \"" + message + "\".")

    def send_to_all_players(self, message):
        # sends message to everyone except GM
        for client in self.clients.values():
            if client.type != ClientTypeTag.GAME_MASTER:
                self.send(client, message)

    def receive(self, client):
        """
        :type client: ClientInfo
        """
        received_data = client.socket.recv(CommunicationServer.DEFAULT_BUFFER_SIZE).decode()
        if len(received_data) < 1:
            raise ConnectionAbortedError
        self.verbose_debug("Message received from " + client.get_tag() + ": \"" + received_data + "\".")
        return received_data

    def disconnect_client(self, client_index):
        try:
            if client_index in self.clients.keys():
                client = self.clients[client_index]
                client.socket.close()
                temp = dict(self.clients)
                del temp[client_index]
                self.clients = temp

        except socket.error as e:
            self.verbose_debug("Couldn't close socket?! " + str(e), True)

    def shutdown(self):
        self.running = False
        self.socket.close()
        self.verbose_debug("Shutting down the server.", True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Use verbose debugging mode.')
    args = vars(parser.parse_args())

    try:
        server = CommunicationServer(args["verbose"])
        server.listen()
    except OSError:
        print("Couldn't start server.")
