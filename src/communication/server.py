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

    def __init__(self, verbose, host=DEFAULT_HOSTNAME, port=DEFAULT_PORT, client_limit=DEFAULT_CLIENT_LIMIT):
        """
        constructor.
        :param verbose:
        :param host:
        :param port:
        """
        self.host = host
        self.port = port
        self.clientLimit = client_limit
        self.socket = socket.socket()
        self.clientDict = {}
        self.clientCount = 0
        self.verbose = verbose
        self.gm_index = -1
        self.registered_games = ""  # Server updates and maintains its own RegisteredGames.xml file
        self.open_games = []  # TODO this should be a list of gameinfos or something that we maintain
        self.xml_message_tag = "{https://se2.mini.pw.edu.pl/17-results/}"
        self.games_id_counter = 0  # For now it's just a counter like player_id used to be
        ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")
        try:
            self.socket.bind((host, port))
        # self.socket.settimeout(CommunicationServer.DEFAULT_TIMEOUT)
        except OSError as e:
            self.verbose_debug("Error while setting up the socket: " + str(e), True)
            sys.exit(0)

        self.verbose_debug("Created server with hostname: " + host + " on port " + str(port), True)
        self.running = True

    def verbose_debug(self, message, important=False):
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
        Thread(target=self.print_state, daemon=True).start()
        Thread(target=self.accept_clients, daemon=True).start()

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
                                print(
                                    " C" + str(client_index) + ": " + str(self.clientDict[client_index].getsockname()))
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
                client_socket.send('0'.encode())
                client_socket.close()
                sleep(1)

    def register_connection(self, client_socket, client_index):
        self.clientDict[client_index] = client_socket
        self.clientCount += 1

        self.verbose_debug(
            "New client: " + str(client_socket.getsockname()) + " with index " + str(client_index) + " connected.",
            True)
        if self.clientCount == self.clientLimit:
            self.verbose_debug("Client capacity reached.")

        thread = Thread(target=self.handle_client, args=(client_socket, client_index))
        thread.daemon = True
        thread.start()

    def handle_client(self, client, client_index):
        """
        Receive and send messages to/from a given client.
        :param client: a client socket
        :param client_index: local index, used in clientDict
        :return:
        """
        '''If is_player true, then the client is a player, and if false then a GM connected.
        Otherwise an undefined client connected and we reject him'''

        # TODO: put some player-specific variables here
        is_player = None
        # TODO:check what the first message from the client was


        # if the message is a "registergame" message, then the client is a gamemaster:
        # self.handle_gm(client, client_index)

        # otherwise, just use the code below

        try:
            if self.running:
                received_data = self.receive(client, Communication.CLIENT_TO_SERVER, client_index)
                if "RegisterGame" in received_data:
                    is_player = False
                elif "GetGames" in received_data:
                    is_player = True

                if is_player is None:
                    self.verbose_debug("Unknown client connected to server, disconnecting him: ", True)
                    raise ConnectionAbortedError
                if is_player:
                    self.verbose_debug("Server has identified client at index: " + str(client_index) + " as a player")
                    Thread(target=self.handle_player, args=(client, client_index, received_data)).start()
                elif not is_player:
                    self.verbose_debug("Server has identified client at index: " + str(client_index) + " as a GM")
                    self.gm_index = client_index
                    Thread(target=self.handle_gm, args=(client, client_index, received_data)).start()

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

    def handle_player(self, client, client_index, first_message):
        # first_message should be a GetGames xml
        while self.registered_games == "":
            # we wait for the registered games to be created until gm registers at least 1 game
            sleep(0.001)
        # We have at least 1 game
        self.send(client, self.registered_games, Communication.SERVER_TO_CLIENT, client_index)
        while self.running:
            received_data = self.receive(client, Communication.CLIENT_TO_SERVER, client_index)
            response = ("Your player message was: " + str(received_data))
            self.send(client, response, Communication.SERVER_TO_CLIENT, client_index)

    def handle_gm(self, client, client_index, first_message):
        # first_message should be a RegisterGames xml
        # Parse first register games msg

        register_games_root = ET.fromstring(first_message)
        num_of_blue_players = 0
        num_of_red_players = 0
        game_name = ""

        for register_game in register_games_root.findall(self.xml_message_tag + "NewGameInfo"):
            game_name = register_game.get("gameName")
            num_of_blue_players = int(register_game.get("blueTeamPlayers"))
            num_of_red_players = int(register_game.get("redTeamPlayers"))

        self.verbose_debug("game_name: " + game_name + " num of blue players: " + str(num_of_blue_players)
                           + " num of red players: " + str(num_of_red_players))
        '''Done parsing RegisterGames msg'''
        #  TODO after we parse RegisterGames.xml we should add a new GameInfo to self.open_games list
        game_registered = self.add_game_to_registered_games(
            game_name=game_name, num_of_blue_players=num_of_blue_players, num_of_red_players=num_of_red_players)

        if game_registered:
            self.send(client, messages.Message().confirmgameregistration(self.games_id_counter),
                      Communication.SERVER_TO_CLIENT, client_index)
            self.games_id_counter += 1
        else:
            self.send(client, messages.Message().reject_game_registration(),
                      Communication.SERVER_TO_CLIENT, client_index)

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
                self.verbose_debug(
                    "Closing connection with C" + str(client_index) + " due to a socket error: " + str(e) + ".", True)
                self.disconnect_client(client_index)
                return False

            except Exception as e:
                self.verbose_debug("Unexpected exception: " + str(e) + ".", True)
                self.disconnect_client(client_index)
                raise e

    def add_game_to_registered_games(self, game_name, num_of_blue_players, num_of_red_players):
        """
        Updates self.register_games xml with a new game
        Returns false if no game was added (rejection), otherwise returns true
        :param game_name: 
        :param num_of_blue_players: 
        :param num_of_red_players: 
        :return: 
        """
        if self.registered_games == "":
            self.registered_games = messages.Message() \
                .registeredgames(gamename=game_name, blueplayers=num_of_blue_players, redplayers=num_of_red_players)
            self.verbose_debug("Updated registered_games: \n" + self.registered_games)
            return True
        else:
            # self.verbose_debug("Looping through: \n" + self.registered_games)
            root = ET.fromstring(self.registered_games)
            #  Reject game registration if game with same name exists
            for games in root.findall(self.xml_message_tag + "GameInfo"):
                existing_game_name = games.get("gameName")
                self.verbose_debug("Existing_game_name: " + existing_game_name)
                if game_name == existing_game_name:
                    self.verbose_debug("Rejecting because game name: " + game_name + " already exists")
                    return False
            my_attributes = {'name': str(game_name), 'blueTeamPlayers': str(num_of_blue_players),
                             'redTeamPlayers': str(num_of_red_players)}
            ET.SubElement(root, 'GameInfo', attrib=my_attributes)
            self.registered_games = ET.tostring(root, encoding='unicode', method='xml')
            self.verbose_debug("Updated registered_games: \n" + self.registered_games)

        return True

    def wait_for_message(self, message_name, client_index, client, max_attempts=10):
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

    def shutdown(self):
        self.running = False
        self.socket.close()
        self.verbose_debug("Shutting down the server.", True)

    def send(self, recipient, message, com_type_flag=Communication.OTHER, client_index=0):
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
                socket.send(message.encode())

        pass

    def receive(self, client, com_type_flag=Communication.OTHER, client_index=0):
        """
        :param client:
        :param com_type_flag: a Communication flag. I am adding this here because it might be useful later.
        """
        received_data = client.recv(CommunicationServer.DEFAULT_BUFFER_SIZE).decode()
        if len(received_data) < 1:
            raise ConnectionAbortedError

        if com_type_flag == Communication.CLIENT_TO_SERVER:
            self.verbose_debug("Message received from C" + str(client_index) + ": \"" + received_data + "\".")
        else:
            pass

        return received_data

    def disconnect_client(self, client_index):
        self.clientDict[client_index].close()
        self.clientDict[client_index] = None
        self.clientCount -= 1


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    args = vars(parser.parse_args())
    server = CommunicationServer(args["verbose"])
    server.listen()
