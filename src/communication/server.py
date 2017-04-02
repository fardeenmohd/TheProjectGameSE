#!/usr/bin/python
import socket
import sys
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from enum import Enum, auto
from threading import Thread
from time import sleep

from src.communication import messages

XML_MESSAGE_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"


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
        self.host = host
        self.port = port
        self.clientLimit = client_limit
        self.socket = socket.socket()
        self.clientDict = {}
        self.clientCount = 0
        self.verbose = verbose
        self.gm_index = -1
        self.registered_games = ""  # Server updates and maintains its own RegisteredGames.xml file
        self.open_games = []  # this should actually be a list of tuples: name, blue players, red players
        self.games_id_counter = 0  # For now it's just a counter like player_id used to be

        ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")
        try:
            self.socket.bind((host, port))

        except OSError as e:
            self.verbose_debug("Error while setting up the socket: " + str(e), True)
            sys.exit(0)

        self.verbose_debug("Created server with hostname: " + host + " on port " + str(port), True)
        self.running = True

    def verbose_debug(self, message, important = False):
        """
        if in verbose mode, print out the given message with a timestamp
        :param message: message to be printed
        :param important: if not in verbose mode, setting this flag to True will make sure this message gets printed
        """
        if self.verbose or important:
            header = "S at " + str(datetime.now().time()) + " - "
            print(header, message)

    def print_state(self):
        """
        method running on a separate Thread, prints the current state of the server every couple of seconds
        time between each printing of debug messages is specified by the constant CommunicationServer.INTER_PRINT_STATE_TIME
        """
        while self.running:
            self.verbose_debug("Currently there are " + str(self.clientCount) + " clients connected.")
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
                    self.verbose_debug("Currently there are " + str(self.clientCount) + " clients connected.", True)

                elif command == "clients":
                    self.verbose_debug("Currently connected clients:", True)
                    if len(self.clientDict) > 0:
                        for client_index in self.clientDict:
                            if self.clientDict[client_index] is not None:
                                print(" C" + str(client_index) + ": " + str(self.clientDict[client_index].getsockname()))
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
        client_index = 0
        while self.running:
            # block and wait until a client connects:
            client_socket, address = self.socket.accept()

            if self.clientCount < self.clientLimit:
                # if client limit not exceeded, handle the new client:
                # send a single byte which says "greetings"
                self.verbose_debug("Accepted some client, sending greeting byte...")
                client_socket.send('1'.encode())
                self.register_connection(client_socket, client_index)
                client_index += 1
            else:
                # if client limit exceeded, send a "sorry, server full" byte:
                client_socket.send('0'.encode())
                client_socket.close()
                sleep(1)

    def register_connection(self, client_socket, client_index):
        self.clientDict[client_index] = client_socket
        self.clientCount += 1

        self.verbose_debug("New client: " + str(client_socket.getsockname()) + " with index " + str(client_index) + " connected.", True)
        if self.clientCount == self.clientLimit:
            self.verbose_debug("Client capacity reached.")

        Thread(target = self.handle_client, args = (client_socket, client_index), daemon = True).start()

    def handle_client(self, client_socket, client_index):
        """
        Receive and send messages to/from a given client.
        :param client_socket: a client socket
        :param client_index: local index, used in clientDict
        :return:
        """

        is_player = None

        # If is_player true, then the client is a player, and if false then a GM connected.
        # Otherwise an undefined client connected and we reject him

        try:
            if self.running:
                # read the first message:
                received_data = self.receive(client_socket, Communication.CLIENT_TO_SERVER, client_index)

                if "RegisterGame" in received_data:
                    is_player = False
                elif "GetGames" in received_data:
                    is_player = True

                if is_player is None:
                    self.verbose_debug("Unknown client connected to server, disconnecting him: ", True)
                    self.disconnect_client(client_index)

                if is_player:
                    self.verbose_debug("Server has identified client at index: " + str(client_index) + " as a player")
                    self.handle_player(client_socket, client_index, received_data)

                elif not is_player:
                    self.verbose_debug("Server has identified client at index: " + str(client_index) + " as a GM")
                    self.gm_index = client_index
                    self.handle_gm(client_socket, client_index, received_data)

        except ConnectionAbortedError:
            self.verbose_debug("C" + str(client_index) + " disconnected. Closing connection.", True)
            self.disconnect_client(client_index)
            return False

        except socket.error as e:
            self.verbose_debug("Closing connection with C" + str(client_index) + " due to a socket error: " + str(e) + ".", True)
            self.disconnect_client(client_index)
            return False

        except Exception as e:
            self.verbose_debug("Disconnecting C" + str(client_index) + " due to an unexpected exception: " + str(e) + ".", True)
            self.disconnect_client(client_index)
            raise e

    def handle_player(self, client, client_index, first_message):
        # # first_message should be a GetGames xml
        # while self.registered_games == "":
        #     # we wait for the registered games to be created until gm registers at least 1 game
        #     sleep(0.001)
        # We have at least 1 game
        self.send(client, messages.registered_games(self.open_games), Communication.SERVER_TO_CLIENT, client_index)

        while self.running:
            received_data = self.receive(client, Communication.CLIENT_TO_SERVER, client_index)
            response = ("Your player message was: " + str(received_data))
            self.send(client, response, Communication.SERVER_TO_CLIENT, client_index)

    def handle_gm(self, client, client_index, first_message):
        # first_message should be a RegisterGames xml
        # Parse first register games msg

        register_games_root = ET.fromstring(first_message)
        blue_players = 0
        red_players = 0
        game_name = ""

        for register_game in register_games_root.findall(XML_MESSAGE_TAG + "NewGameInfo"):
            game_name = register_game.get("gameName")
            blue_players = int(register_game.get("blueTeamPlayers"))
            red_players = int(register_game.get("redTeamPlayers"))

        self.verbose_debug("GM" + str(client_index) + " registered a new game, with name: " + game_name + " num of blue players: " + str(
            blue_players) + " num of red players: " + str(red_players))

        # done parsing.

        game_registered = self.register_game(game_name, blue_players, red_players)

        if game_registered:
            self.send(client, messages.confirm_game_registration(self.games_id_counter), Communication.SERVER_TO_CLIENT, client_index)
            self.games_id_counter += 1
        else:
            self.send(client, messages.reject_game_registration(), Communication.SERVER_TO_CLIENT, client_index)

        # after registering the game, this GM will be waiting until players join it.

        while self.running:
            try:
                received_data = self.receive(client, Communication.CLIENT_TO_SERVER, client_index)
                response = ("Your GM message was: " + str(received_data))
                self.send(client, response, Communication.SERVER_TO_CLIENT, client_index)

            except ConnectionAbortedError:
                self.verbose_debug("C" + str(client_index) + " disconnected. Closing connection.", True)
                self.disconnect_client(client_index)
                return False

            except socket.error as e:
                self.verbose_debug("Closing connection with C" + str(client_index) + " due to a socket error: " + str(e) + ".", True)
                self.disconnect_client(client_index)
                return False

            except Exception as e:
                self.verbose_debug("Unexpected exception: " + str(e) + ".", True)
                self.disconnect_client(client_index)
                raise e

    def register_game(self, game_name, blue_players, red_players):
        """
        Updates self.register_games xml with a new game
        Returns false if no game was added (rejection), otherwise returns true
        :param game_name:
        :param blue_players:
        :param red_players:
        :return:
        """
        if len(self.open_games) == 0:
            self.open_games.append((game_name, blue_players, red_players))

        else:
            for game in self.open_games:
                if game[0] == game_name:
                    self.verbose_debug("Rejecting registration, because game name: " + game_name + "already exists")
                    return False
            self.open_games.append((game_name, blue_players, red_players))

        self.verbose_debug("Currently registered_games: \n" + str(self.open_games))
        return True

    def wait_for_message(self, message_name, client_index, client, max_attempts = 10):
        """
        This method blocks until it receives a certain message, it will try max_attempts amount of times to receive it
        Then it returns the full message when it is received
        :param message_name:
        :param client_index:
        :param client:
        :param max_attempts:
        :return:
        """
        received_data = self.receive(client, Communication.CLIENT_TO_SERVER, client_index)
        attempts = 1
        while message_name not in received_data and self.running and attempts <= max_attempts:
            received_data = self.receive(client, Communication.CLIENT_TO_SERVER, client_index)
            attempts += 1
        return received_data

    def send(self, recipient, message, com_type_flag = Communication.OTHER, client_index = 0):
        """
        a truly vital method. Sends a given message to a recipient.
        :param recipient: socket object of the recipient.
        :param message: message to be passed, any type. will be encoded as string.
        :param com_type_flag: a Communication flag. I am adding this here because it might be useful later.
        """
        message = str(message)
        recipient.send(message.encode())

        if com_type_flag == Communication.SERVER_TO_CLIENT:
            self.verbose_debug("Message sent to C" + str(client_index) + ": \"" + message + "\".")
        else:
            pass

    def send_to_all_players(self, message):
        # sends message to everyone except GM
        for client_index, socket in self.clientDict.items():
            if client_index != self.gm_index:
                self.send(socket, message, Communication.SERVER_TO_CLIENT, client_index)

        pass

    def receive(self, client, com_type_flag = Communication.OTHER, client_index = 0):
        """
        :param client:
        :param com_type_flag: a Communication flag. I am adding this here because it might be useful later.
        """
        try:
            received_data = client.recv(CommunicationServer.DEFAULT_BUFFER_SIZE).decode()
            if len(received_data) < 1:
                raise ConnectionAbortedError
        except ConnectionAbortedError:
            self.verbose_debug("C" + str(client_index) + " disconnected. Closing connection.", True)
            self.disconnect_client(client_index)
            return False

        except socket.error as e:
            self.verbose_debug(
                "Closing connection with C" + str(client_index) + " due to a socket error: " + str(e) + ".", True)
            self.disconnect_client(client_index)
            return False

        except Exception as e:
            self.verbose_debug("Unexpected exception: " + str(e) + ".", True)
            self.disconnect_client(client_index)
            raise e

        if com_type_flag == Communication.CLIENT_TO_SERVER:
            self.verbose_debug("Message received from C" + str(client_index) + ": \"" + received_data + "\".")
        else:
            pass

        return received_data

    def disconnect_client(self, client_index):
        self.clientDict[client_index].close()
        # self.clientDict[client_index] = None
        self.clientCount -= 1

    def shutdown(self):
        self.running = False
        self.socket.close()
        self.verbose_debug("Shutting down the server.", True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Use verbose debugging mode.')
    args = vars(parser.parse_args())
    server = CommunicationServer(args["verbose"])
    server.listen()
