#!/usr/bin/python
import socket
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from time import sleep

from src.communication import messages
from src.communication.info import ClientInfo, GameInfo, ClientTypeTag
from src.communication.unexpected import UnexpectedClientMessage

XML_MESSAGE_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"
ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")


class CommunicationServer:
    # some constants:
    INTER_PRINT_STATE_TIME = 5
    DEFAULT_BUFFER_SIZE = 2048
    DEFAULT_PORT = 420
    DEFAULT_TIMEOUT = 10
    DEFAULT_HOSTNAME = socket.gethostname()

    # below list contains messages which are addressed to a different player, NOT GM
    TO_PLAYER_MESSAGES = ["Data", "KnowledgeExchangeRequest", "AcceptExchangeRequest",
                          "RejectKnowledgeExchange"]

    def __init__(self, verbose: bool, hostname: str = DEFAULT_HOSTNAME, port: int = DEFAULT_PORT):
        """
        constructor.
        :param verbose:
        :param hostname:
        :param port:
        """

        # declare fields:
        self.running = True
        self.host = hostname
        self.port = port
        self.verbose = verbose

        self.socket = socket.socket()
        self.clients = {}  # client_id => ClientInfo object
        self.games = {}  # game_id => GameInfo object
        self.client_indexer = 0
        self.games_indexer = 0

        try:
            self.socket.bind((hostname, port))

        except OSError as e:
            self.verbose_debug("Error while setting up the socket: " + str(e), True)
            raise e

        self.verbose_debug("Created server with hostname: " + hostname + " on port " + str(port), True)

    def verbose_debug(self, message: str, important: bool = False):
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
        time between each printing of debug messages is specified by the constant NTER_PRINT_STATE_TIME
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
            self.register_connection(client_socket, str(self.client_indexer))
            self.client_indexer += 1

    def register_connection(self, client_socket: socket, client_id: str):
        new_client = ClientInfo(client_id, socket=client_socket)
        self.clients[client_id] = new_client

        self.verbose_debug(
            "New client: " + new_client.get_tag() + " with address " + str(client_socket.getsockname()) + " connected.")

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
                    new_client.tag = ClientTypeTag.GAME_MASTER
                elif "GetGames" in received_data:
                    new_client.tag = ClientTypeTag.PLAYER

                if new_client.tag == ClientTypeTag.CLIENT:
                    self.verbose_debug("Unknown client connected to server, disconnecting him: ", True)
                    self.disconnect_client(new_client.id)

                if new_client.tag == ClientTypeTag.PLAYER:
                    self.verbose_debug("Identified C" + str(new_client.id) + " as a player")
                    self.handle_player(new_client)

                elif new_client.tag == ClientTypeTag.GAME_MASTER:
                    self.verbose_debug("Identified " + new_client.get_tag() + " as a Game Master")
                    self.handle_gm(new_client, received_data)

        except (ConnectionAbortedError, ConnectionResetError):
            self.disconnect_client(new_client.id)

        except Exception as e:
            self.verbose_debug(
                "Disconnecting " + new_client.get_tag() + " due to an unexpected exception: " + str(e) + ".", True)
            self.disconnect_client(new_client.id)
            raise e

    def handle_player(self, player: ClientInfo):
        # first_message was a GetGames xml, so let's get all the open games:
        open_games = {}
        for game in self.games.values():
            if game.open:
                open_games[game.id] = game

        # and send them to this player
        self.send(player, messages.RegisteredGames(open_games))

        while self.running:
            player_message = self.receive(player)
            message_root = ET.fromstring(player_message)

            if player_message is None:
                raise ConnectionAbortedError

            # parse the message:
            if "JoinGame" in player_message:
                self.handle_join(player, player_message)

            elif any(message in player_message for message in self.TO_PLAYER_MESSAGES):
                self.send(self.clients[message_root.attrib["playerId"]], player_message)

            elif "GetGames" in player_message:
                # he's trying to re-join so let's handle him again!
                self.handle_player(player)

            else:
                # DEFAULT HANDLING: relay the message to GM
                self.send(self.clients[player.game_master_id], player_message)

    def handle_join(self, player, player_message):
        message_root = ET.fromstring(player_message)
        # check if game with this name exists:
        players_game_name = message_root.attrib["gameName"]

        for game_index, game_info in self.games.items():
            if game_info.name == players_game_name:
                # game found, so we will update JoinGame with player_id and send it to GM:
                message_root.attrib["playerId"] = str(player.id)
                join_game_message = ET.tostring(message_root, encoding='unicode', method='xml')

                gm_id = game_info.game_master_id
                player.game_master_id = gm_id
                player.game_id = self.clients[gm_id].game_id
                self.send(self.clients[gm_id], join_game_message)
                return True
        # no game with this name, send rejection
        self.send(player, messages.RejectJoiningGame(player.id, players_game_name))
        return False

    def handle_gm(self, gm: ClientInfo, registration_msg: str):
        # first_message should be a RegisterGames xml

        if not self.try_register_game(gm, registration_msg):
            # registration failed. send rejection:
            self.send(gm, messages.RejectGameRegistration(gm.game_name))

            # GM will be trying again, so let's wait for his second attempt:
            second_attempt_message = self.receive(gm)
            if not self.try_register_game(gm, second_attempt_message):
                # registration failed, again. send rejection:
                self.send(gm, messages.RejectGameRegistration(gm.game_name))
                # gm should not try to register anymore, so if we receive any message now then it's an error:
                should_not_be_a_message = self.receive(gm)
                if len(should_not_be_a_message) > 0:
                    raise UnexpectedClientMessage(
                        "GameMaster tried to register a game again, while he should have switched off!")
        else:
            ###############REGISTERING GAME DONE###################
            # Now we handle the GM's rejection or confirmation, as well as other messsages in a while loop
            while self.running and gm.id in self.clients.keys():
                gm_msg = self.receive(gm)

                if gm_msg is None:
                    raise ConnectionAbortedError

                msg_root = ET.fromstring(gm_msg)

                # non-default message types:
                if "ConfirmJoiningGame" in gm_msg:
                    player_id = msg_root.attrib["playerId"]
                    self.clients[player_id].game_master_id = gm.id
                    self.send(self.clients[player_id], gm_msg)

                elif "GameStarted" in gm_msg:
                    game_id = msg_root.attrib["gameId"]
                    self.games[game_id].open = False

                elif "Data" in gm_msg:
                    player_id = msg_root.attrib["playerId"]
                    finished = msg_root.attrib["gameFinished"]
                    if finished == "true":
                        del self.games[self.clients[player_id].game_id]
                        pass
                    client = self.clients.get(player_id)
                    if client is not None:
                        self.send(client, gm_msg)


                else:
                    # DEFAULT MESSAGE HANDLING:
                    self.relay_msg_to_player(gm_msg)

    def try_register_game(self, gm: ClientInfo, register_game_message: str):
        """
        Read a RegisterGame message, try to add it to our games list if no game with the same name exists.
        :type gm: ClientInfo
        :param register_game_message: string containing a RegisterGame message
        :returns True, if succeeded, False if it didnt
        """
        if register_game_message is None:
            raise ConnectionAbortedError
        register_games_root = ET.fromstring(register_game_message)

        new_game_info = register_games_root[0]  # access index 0 because info is in the first (and only) child of root

        new_game_name = new_game_info.attrib["gameName"]
        new_blue_players = new_game_info.attrib["blueTeamPlayers"]
        new_red_players = new_game_info.attrib["redTeamPlayers"]
        # done parsing.

        gm.game_name = new_game_name

        # check if game with this name exists:
        if len([game for game_index, game in self.games.items() if game.name == new_game_name]) > 0:
            # reject the registration.
            self.verbose_debug(
                gm.get_tag() + " tried to register a game: \"" + new_game_name + "\". Rejecting, because name is taken.")
            return False

        else:
            # create the new game:
            game_id = str(self.games_indexer)
            self.games[game_id] = GameInfo(id=game_id, name=new_game_name, max_blue_players=new_blue_players,
                                           max_red_players=new_red_players,
                                           open=True, game_master_id=gm.id)
            gm.game_id = game_id
            self.verbose_debug(
                gm.get_tag() + " registered a new game, with name: " + new_game_name + " num of blue players: " + str(
                    new_blue_players) + " num of red players: " + str(new_red_players))
            self.send(gm, messages.ConfirmGameRegistration(game_id))
            self.games_indexer += 1
            return True

    def relay_msg_to_player(self, gm_msg):
        # the message should be a "PlayerMessage", so it definitely needs to have playerId in root attributes.
        msg_root = ET.fromstring(gm_msg)
        player_id = msg_root.attrib["playerId"]
        client = self.clients.get(player_id)
        if client is not None:
            self.send(client, gm_msg)

    def send(self, recipient: ClientInfo, message: str):
        """
        a truly vital method. Sends a given message to a recipient.
        :type recipient: ClientInfo
        :param recipient: socket object of the recipient.
        :param message: message to be passed, any type. will be encoded as string.
        """
        message = str(message)
        recipient.socket.send(message.encode())
        sleep(0.001)
        self.verbose_debug("Message sent to " + recipient.get_tag() + ": \"" + message + "\".")

    def send_to_all_players(self, message: str):
        # sends message to everyone except GM
        for client in self.clients.values():
            if client.tag != ClientTypeTag.GAME_MASTER:
                self.send(client, message)

    def receive(self, client: ClientInfo):
        """
        :type client: ClientInfo
        """

        # check if the client hadn't disconnected before we can read a message:
        if client.id not in self.clients.keys():
            raise ConnectionResetError
        try:
            received_data = client.socket.recv(CommunicationServer.DEFAULT_BUFFER_SIZE).decode()
            if len(received_data) < 1 or received_data is None:
                raise ConnectionResetError

            self.verbose_debug("Message received from " + client.get_tag() + ": \"" + received_data + "\".")
            sleep(0.01)
            return received_data

        except (ConnectionAbortedError, ConnectionResetError) as e:
            self.verbose_debug(client.get_tag() + " disconnected. Closing connection.", True)
            self.disconnect_client(client.id)
            raise e

    def disconnect_client(self, client_id: int):

        if client_id not in self.clients.keys():
            return
        client = self.clients[client_id]

        # if the client was a GM, remove his game from server:
        if client.tag == ClientTypeTag.GAME_MASTER:
            for game_info in self.games.values():
                if game_info.name == client.game_name and game_info.game_master_id == client_id:
                    # find all players who were connected to this game and send them a GameMasterdisconneted message
                    for dude in self.clients.values():
                        if dude.tag == ClientTypeTag.PLAYER and dude.game_master_id == client.id:
                            self.send(dude, messages.GameMasterDisconnected(game_info.id))

                    del self.games[game_info.id]
                    self.verbose_debug("Closed " + client.get_tag() + "'s game (name was: " + game_info.name + ").")
                    break
            else:
                self.verbose_debug(
                    "Couldn't close " + client.get_tag() + "'s game - it wasn't found on the server.")

        # close the socket
        try:
            client.socket.close()
            temp = dict(self.clients)
            del temp[client_id]
            self.clients = temp

        except socket.error as e:
            self.verbose_debug("Couldn't close socket?! " + str(e), True)

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
