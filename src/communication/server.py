#!/usr/bin/python
import socket
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from time import sleep

from src.communication import messages_old, messages_new
from src.communication.info import ClientInfo, GameInfo, ClientTypeTag
from src.communication.unexpected import UnexpectedClientMessage

XML_MESSAGE_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"
ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")


class CommunicationServer:
    # some constants:
    INTER_PRINT_STATE_TIME = 5
    DEFAULT_BUFFER_SIZE = 1024
    DEFAULT_PORT = 420
    DEFAULT_TIMEOUT = 10
    DEFAULT_CLIENT_LIMIT = 10
    DEFAULT_HOSTNAME = socket.gethostname()

    def __init__(self, verbose: bool, host: str=DEFAULT_HOSTNAME, port: int=DEFAULT_PORT,
                 client_limit: int=DEFAULT_CLIENT_LIMIT):
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

    def verbose_debug(self, message: str, important: bool=False):
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

        Thread(target=self.print_state, daemon=True).start()
        Thread(target=self.accept_clients, daemon=True).start()

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

    def register_connection(self, client_socket: socket, client_id: int):
        new_client = ClientInfo(client_id, socket=client_socket)
        self.clients[client_id] = new_client

        self.verbose_debug(
            "New client: " + new_client.get_tag() + " with address " + str(client_socket.getsockname()) + " connected.")
        if len(self.clients) == self.clientLimit:
            self.verbose_debug("Client capacity reached.")

        Thread(target=self.handle_client, args=[new_client], daemon=True).start()

    def handle_client(self, new_client: ClientInfo):
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
            self.disconnect_client(new_client.id)

        except Exception as e:
            self.verbose_debug(
                "Disconnecting " + new_client.get_tag() + " due to an unexpected exception: " + str(e) + ".", True)
            self.disconnect_client(new_client.id)
            raise e

    def handle_player(self, player: ClientInfo):
        # first_message was a GetGames xml
        self.send(player, messages_new.registered_games(self.games))
        players_game_name = ""
        while self.running:
            received = self.receive(player)

            if received is None:
                raise ConnectionAbortedError

            # parse the message, relay it to GM

            if "JoinGame" in received:
                join_game_root = ET.fromstring(received)

                # check if game with this name exists:
                players_game_name = join_game_root.attrib["gameName"]

                for game_index, game_info in self.games.items():
                    if game_info.name == players_game_name:
                        # game found, so we will update JoinGame with player_id and send it to GM:
                        join_game_root.attrib["playerId"] = str(player.id)
                        join_game_message = ET.tostring(join_game_root, encoding='unicode', method='xml')

                        # find the right GM:
                        self.relay_msg_to_gm(join_game_message, players_game_name)

                    else:
                        # no game with this name, send rejection
                        self.send(player, messages_new.reject_joining_game(player.id, players_game_name))

            elif "KnowledgeExchangeRequest" in received or "Data" in received:
                knowledge_exchanged_root = ET.fromstring(received)
                self.send(self.clients[int(knowledge_exchanged_root.attrib["playerId"])], received)

            else:
                self.relay_msg_to_gm(received, players_game_name)

    def handle_gm(self, gm: ClientInfo, registration_msg: str):
        # first_message should be a RegisterGames xml

        if not self.try_register_game(gm, registration_msg):
            # registration failed. send rejection:
            self.send(gm, messages_new.reject_game_registration(gm.game_name))

            # GM will be trying again, so let's wait for his second attempt:
            second_attempt_message = self.receive(gm)
            if not self.try_register_game(gm, second_attempt_message):
                # registration failed, again. send rejection:
                self.send(gm, messages_new.reject_game_registration(gm.game_name))
                # gm should not try to register anymore, so if we receive any message now then it's an error:
                should_not_be_a_message = self.receive(gm)
                if len(should_not_be_a_message) > 0:
                    raise UnexpectedClientMessage(
                        "GameMaster tried to register a game again, while he should have switched off!")

        ###############REGISTERING GAME DONE###################
        # Now we handle the GM's rejection or confirmation, as well as other messsages in a while loop
        while self.running:
            # TODO move this code to a handle_gm_msg function?
            gm_msg = self.receive(gm)

            if gm_msg is None:
                raise ConnectionAbortedError

            if "ConfirmJoiningGame" in gm_msg:
                confirm_root = ET.fromstring(gm_msg)
                self.send(self.clients[int(confirm_root.attrib.get("playerId"))], gm_msg)
            elif "RejectJoiningGame" in gm_msg:
                reject_root = ET.fromstring(gm_msg)
                self.send(self.clients[int(reject_root.attrib.get("playerId"))], gm_msg)
            else:
                # TODO handle other messages here
                gm_msg = self.receive(gm)
                self.send_to_all_players(gm_msg)
                # then, he will send us a GameStarted message
                # TODO: parse a GameStarted message

                # TODO: relay other messages to players etc.

    def try_register_game(self, gm: ClientInfo, register_game_message: str):
        """
        Read a RegisterGame message, try to add it to our games list if no game with the same name exists.
        :type gm: ClientInfo
        :param register_game_message: string containing a RegisterGame message
        :returns True, if succeeded, False if it didnt
        """
        register_games_root = ET.fromstring(register_game_message)

        new_game_info = register_games_root[0]  # access index 0 because info is in the first (and only) child of root

        new_game_name = new_game_info.attrib["gameName"]
        new_blue_players = new_game_info.attrib["blueTeamPlayers"]
        new_red_players = new_game_info.attrib["redTeamPlayers"]
        # done parsing.

        # check if game with this name exists:
        if len([game for game_index, game in self.games.items() if game.name == new_game_name]) > 0:
            # reject the registration.
            self.verbose_debug(
                gm.get_tag() + " tried to register a game with name: \"" + new_game_name + "\". Rejecting, because there "
                                                                                           "already is a game with this "
                                                                                           "name.")
            return False

        else:
            # create the new game:
            self.games[self.games_indexer] = GameInfo(id=self.games_indexer, name=new_game_name,
                                                      blue_players=new_blue_players, red_players=new_red_players,
                                                      open=True)
            gm.game_name = new_game_name
            self.verbose_debug(
                gm.get_tag() + " registered a new game, with name: " + new_game_name + " num of blue players: " + str(
                    new_blue_players) + " num of red players: " + str(new_red_players))
            self.send(gm, messages_new.confirm_game_registration(self.games[self.games_indexer].id))
            self.games_indexer += 1
            return True

    def wait_for_message(self, message_name: str, client, max_attempts: int=10):
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

    def relay_msg_to_gm(self, msg: str, game_name: str):
        """
        Relays msg to the GM handling the same game name as game_name
        :param msg: message to be sent as string
        :param game_name: name of GM's game
        :return:
        """
        for client_index, client in self.clients.items():
            if client.type == ClientTypeTag.GAME_MASTER and client.game_name == game_name:
                self.send(client, msg)

    def send(self, recipient: ClientInfo, message: str):
        """
        a truly vital method. Sends a given message to a recipient.
        :type recipient: ClientInfo
        :param recipient: socket object of the recipient.
        :param message: message to be passed, any type. will be encoded as string.
        """
        message = str(message)
        recipient.socket.send(message.encode())
        self.verbose_debug("Message sent to " + recipient.get_tag() + ": \"" + message + "\".")

    def send_to_all_players(self, message: str):
        # sends message to everyone except GM
        for client in self.clients.values():
            if client.type != ClientTypeTag.GAME_MASTER:
                self.send(client, message)

    def receive(self, client: ClientInfo):
        """
        :type client: ClientInfo
        """
        try:
            received_data = client.socket.recv(CommunicationServer.DEFAULT_BUFFER_SIZE).decode()
            if len(received_data) < 1 or received_data is None:
                raise ConnectionAbortedError
            self.verbose_debug("Message received from " + client.get_tag() + ": \"" + received_data + "\".")
            return received_data

        except (ConnectionAbortedError, ConnectionResetError):
            self.verbose_debug(client.get_tag() + " disconnected. Closing connection.", True)
            self.disconnect_client(client.id)

    def disconnect_client(self, client_index: int):

        if client_index not in self.clients.keys():
            return

        client = self.clients[client_index]
        # close the socket
        try:
            client.socket.close()
            temp = dict(self.clients)
            del temp[client_index]
            self.clients = temp

        except socket.error as e:
            self.verbose_debug("Couldn't close socket?! " + str(e), True)

            # if the client was a GM, remove his game from server:
        if client.type == ClientTypeTag.GAME_MASTER:
            for game_info in self.games.values():
                if game_info.name == client.game_name:
                    del self.games[game_info.id]
                    self.verbose_debug("Closed " + client.get_tag() + "'s game (name was: " + game_info.name + ").")
                    break
            else:
                self.verbose_debug("Couldn't close " + client.get_tag() + "'s game - it wasn't found on the server.")

    def shutdown(self):
        self.running = False
        self.socket.close()
        self.verbose_debug("Shutting down the server.", True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    args = vars(parser.parse_args())

    try:
        server = CommunicationServer(args["verbose"])
        server.listen()
    except OSError:
        print("Couldn't start server.")
