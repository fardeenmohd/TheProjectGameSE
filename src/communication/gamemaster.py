import copy
import os
import uuid
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from random import random, randint
from threading import Thread
from time import sleep

from src.communication import messages
from src.communication.client import Client
from src.communication.info import GameInfo, Direction, GoalFieldInfo, Allegiance, PieceInfo, PieceType, \
    GoalFieldType, ClientTypeTag, PlayerType, PlayerInfo
from src.communication.unexpected import UnexpectedServerMessage

GAME_SETTINGS_TAG = "{https://se2.mini.pw.edu.pl/17-pl-19/17-pl-19/}"
XML_MESSAGE_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"
ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")


def parse_game_master_settings():
    full_file = os.getcwd() + "\GameMasterSettings.xml"
    tree = ET.parse(full_file)
    root = tree.getroot()

    return root


class GameMaster(Client):
    def parse_game_definition(self):
        root = parse_game_master_settings()

        self.keep_alive_interval = int(root.attrib.get('KeepAliveInterval'))
        self.retry_register_game_interval = int(root.attrib.get('RetryRegisterGameInterval'))

        goals = {}

        board_width = 0
        task_area_length = 0
        goal_area_length = 0

        for game_attributes in root.findall(GAME_SETTINGS_TAG + "GameDefinition"):
            # load goal field information:
            for goal in game_attributes.findall(GAME_SETTINGS_TAG + "Goals"):
                colour = goal.get("team")
                x = int(goal.get("x"))
                y = int(goal.get("y"))
                goals[x, y] = GoalFieldInfo(x, y, colour, type=GoalFieldType.GOAL)

            self.sham_probability = float(game_attributes.find(GAME_SETTINGS_TAG + "ShamProbability").text)
            self.placing_pieces_frequency = int(
                game_attributes.find(GAME_SETTINGS_TAG + "PlacingNewPiecesFrequency").text)
            self.initial_number_of_pieces = int(game_attributes.find(GAME_SETTINGS_TAG + "InitialNumberOfPieces").text)
            board_width = int(game_attributes.find(GAME_SETTINGS_TAG + "BoardWidth").text)
            task_area_length = int(game_attributes.find(GAME_SETTINGS_TAG + "TaskAreaLength").text)
            goal_area_length = int(game_attributes.find(GAME_SETTINGS_TAG + "GoalAreaLength").text)

            self.game_name = game_attributes.find(GAME_SETTINGS_TAG + "GameName").text
            self.team_limit = int(game_attributes.find(GAME_SETTINGS_TAG + "NumberOfPlayersPerTeam").text)

        self.info = GameInfo(goal_fields=goals, board_width=board_width, task_height=task_area_length,
                             goals_height=goal_area_length, max_blue_players=self.team_limit,
                             max_red_players=self.team_limit)

    def parse_action_costs(self):
        root = parse_game_master_settings()

        for action_costs in root.findall(GAME_SETTINGS_TAG + "ActionCosts"):
            self.move_delay = int(action_costs.find(GAME_SETTINGS_TAG + "MoveDelay").text)
            self.discover_delay = int(action_costs.find(GAME_SETTINGS_TAG + "DiscoverDelay").text)
            self.test_delay = int(action_costs.find(GAME_SETTINGS_TAG + "TestDelay").text)
            self.pickup_delay = int(action_costs.find(GAME_SETTINGS_TAG + "PickUpDelay").text)
            self.placing_delay = int(action_costs.find(GAME_SETTINGS_TAG + "PlacingDelay").text)
            self.knowledge_exchange_delay = int(action_costs.find(GAME_SETTINGS_TAG + "KnowledgeExchangeDelay").text)

    def __init__(self, verbose=False):
        super().__init__(verbose=verbose)

        self.RANDOMIZATION_ATTEMPTS = 10
        self.piece_indexer = 0
        self.typeTag = ClientTypeTag.GAME_MASTER
        self.game_on = False
        self.player_indexer = 0

        self.parse_game_definition()
        self.parse_action_costs()

    def run(self):
        register_game_message = messages.RegisterGame(self.game_name, self.team_limit, self.team_limit)
        self.send(register_game_message)

        message = self.receive()

        try:
            if "RejectGameRegistration" in message:
                sleep(self.retry_register_game_interval)
                self.send(register_game_message)

            elif "ConfirmGameRegistration" in message:
                # read game id from message
                confirmation_root = ET.fromstring(message)
                self.info.id = confirmation_root.attrib.get("gameId")

                while True:
                    # now, we will be receiving messages about players who are trying to join:
                    message = self.receive()  # this will block

                    if "JoinGame" in message:
                        self.handle_join(message)

                        if self.get_num_of_players() == self.team_limit * 2:
                            #  We are ready to start the game
                            self.send(messages.GameStarted(self.info.id))
                            self.set_up_game()
                            self.game_on = True
                            self.play()

                    else:
                        raise UnexpectedServerMessage

        except UnexpectedServerMessage:
            self.verbose_debug("Shutting down due to unexpected message: " + message)
            self.shutdown()

        except (ConnectionAbortedError, ConnectionResetError) as e:
            self.verbose_debug("Server shut down or other type of connection error: " + str(e))
            self.shutdown()

    def handle_join(self, message):
        # a player is trying to join! let's parse his message
        joingame_root = ET.fromstring(message)

        in_player_id = joingame_root.attrib.get("playerId")
        in_game_name = joingame_root.attrib.get("gameName")
        in_pref_team = joingame_root.attrib.get("preferredTeam")
        in_pref_role = joingame_root.attrib.get("preferredRole")

        # in theory, received game name has to be the same as our game, it should be impossible otherwise
        self.verbose_debug("A player is trying to join, with id: " + in_player_id + ".")
        if in_game_name != self.game_name:
            self.verbose_debug("The server somehow sent us a message with the wrong game name.")
            raise UnexpectedServerMessage

        # let's see if we can fit the player at all:
        if self.get_num_of_players() == self.team_limit * 2:
            # he can't fit in, send a rejection message :(
            self.verbose_debug("Player " + in_player_id + " was rejected, because the game is already full.")
            self.send(messages.RejectJoiningGame(in_player_id, self.game_name))
            return False

        # generating the private GUID
        private_guid = str(uuid.uuid4())

        # add him to a team while taking into account his preferences:
        team_color, role = self.add_player(in_player_id, in_pref_role, in_pref_team, private_guid)

        self.verbose_debug("Player with id " + in_player_id + " was accepted to game, assigned type of " + role
                           + " in team " + team_color + ".")

        self.send(messages.ConfirmJoiningGame(in_player_id, str(self.info.id), private_guid, team_color, role))

    def set_up_game(self):
        # now that the players have connected, we can prepare the game
        self.info.initialize_fields()

        # place the players:
        for player_id in self.info.teams[Allegiance.RED.value].keys():
            x = randint(0, self.info.board_width - 1)
            y = randint(self.info.whole_board_length - self.info.goals_height + 1, self.info.whole_board_length)
            random_red_goal_field = self.info.goal_fields[x, y]
            while random_red_goal_field.is_occupied:
                x = randint(0, self.info.board_width - 1)
                y = randint(self.info.whole_board_length - self.info.goals_height + 1, self.info.whole_board_length)
                random_red_goal_field = self.info.goal_fields[x, y]

            self.info.goal_fields[x, y].player_id = player_id
            self.info.teams[Allegiance.RED.value][player_id].location = (x, y)

        for player_id in self.info.teams[Allegiance.BLUE.value].keys():
            x = randint(0, self.info.board_width - 1)
            y = randint(0, self.info.goals_height - 1)
            random_blue_goal_field = self.info.goal_fields[x, y]
            while random_blue_goal_field.is_occupied:
                x = randint(0, self.info.board_width - 1)
                y = randint(0, self.info.goals_height - 1)
                random_blue_goal_field = self.info.goal_fields[x, y]

            self.info.goal_fields[x, y].player_id = player_id
            self.info.teams[Allegiance.BLUE.value][player_id].location = (x, y)

        # create the first pieces:
        for i in range(self.initial_number_of_pieces):
            self.add_piece()

    def place_pieces(self):
        while self.game_on:
            sleep(float(self.placing_pieces_frequency) / 1000)
            self.add_piece()

    def add_piece(self):
        piece_id = str(self.piece_indexer)

        # check if we can add the piece at all:
        if not self.info.check_for_empty_task_fields():
            return False

        # randomize until we find a suitable field:

        x = randint(0, self.info.board_width - 1)
        y = randint(self.info.goals_height, self.info.task_height - 1)

        i = 0
        while self.info.has_piece(x, y) and i < self.RANDOMIZATION_ATTEMPTS:
            x = randint(0, self.info.board_width - 1)
            y = randint(self.info.goals_height, self.info.task_height - 1)
            i += 1

        if self.info.has_piece(x, y):
            for task_field in self.info.task_fields:
                if not task_field.has_piece():
                    x = task_field.x
                    y = task_field.y
                    break

        new_piece = PieceInfo(piece_id, datetime.now())

        if random() >= self.sham_probability:
            new_piece.piece_type = PieceType.NORMAL
        else:
            new_piece.piece_type = PieceType.SHAM

        found_field = self.info.task_fields[x, y]
        # update distance_to_piece in all fields:
        for field in self.info.task_fields.values():
            distance = self.info.manhattan_distance(field, found_field)
            if field.distance_to_piece == -1 or field.distance_to_piece > distance:
                field.distance_to_piece = distance

        self.info.task_fields[x, y].piece_id = piece_id
        self.info.pieces[piece_id] = new_piece
        self.piece_indexer += 1
        self.verbose_debug(
            "Added a " + new_piece.piece_type + " piece with id: " + piece_id + "at coordinates " + str(x) + ", " + str(
                y) + ".")

    def add_player(self, player_id, pref_role, pref_team, private_guid):
        """
        :returns: a tuple: (team, type)
        """

        if len(self.info.teams[pref_team]) == self.team_limit:
            if pref_team == Allegiance.BLUE.value:
                team = Allegiance.RED.value
            else:
                team = Allegiance.BLUE.value
        else:
            team = pref_team

        if pref_role == PlayerType.LEADER.value:
            for player in self.info.teams[team].values():
                if player.type == PlayerType.LEADER.value:
                    role = PlayerType.MEMBER.value
                    break
            else:
                role = PlayerType.LEADER.value
        else:
            role = PlayerType.MEMBER.value

        self.info.teams[team][player_id] = PlayerInfo(player_id, team, type=role, guid=private_guid)
        return team, role

    def find_player_by_guid(self, guid):
        for team in self.info.teams.values():
            for player in team:
                if team[player].guid == guid:
                    return team[player]

    def find_player_by_id(self, id):
        for team in self.info.teams.values():
            for player in team:
                if team[player].id == id:
                    return team[player]

    def handle_move_message(self, move_message):

        sleep(float(self.move_delay) / 1000)

        root = ET.fromstring(move_message)

        guid = root.get('playerGuid')
        direction = root.get('direction')
        player_info = self.find_player_by_guid(guid)
        player_location = player_info.location
        new_location = player_location
        piece_dict = None

        if direction == Direction.UP.value:
            new_location[1] += 1

        if direction == Direction.DOWN.value:
            new_location[1] -= 1

        if direction == Direction.LEFT.value:
            new_location[0] -= 1

        if direction == Direction.RIGHT.value:
            new_location[0] += 1

        if self.info.is_task_field(new_location):
            new_task_field = self.info.task_fields[new_location]

            if new_task_field.is_occupied():
                # can't move, stay in the same location.
                new_location = player_info.location

            if new_task_field.has_piece(new_location):
                piece_id = new_task_field.piece_id

                # check if the Player already knows what type this piece is:
                # if yes, keep his information about it:
                piece_info = self.info.teams[player_info.team][player_info.id].info.pieces.get(piece_id)
                if piece_info is None:
                    # if he doesn't yet know about the Piece, set its type to unknown
                    self.info.teams[player_info.team][player_info.id].info.pieces[piece_id] = PieceInfo(piece_id,
                                                                                                        piece_type=PieceType.UNKNOWN.value)
                    piece_info = self.info.teams[player_info.team][player_info.id].info.pieces.get(piece_id)

                piece_dict = {piece_id: piece_info}

                # finally, send the message.
            self.send(messages.Data(player_info.id, self.info.finished, task_fields={new_location: new_task_field},
                                    pieces=piece_dict, player_location=new_location))

        elif self.info.is_goal_field(new_location):

            new_goal_field = copy.deepcopy(self.info.goal_fields[new_location])
            if new_goal_field.is_occupied():
                new_location = player_info.location

            # use the type that the player knows.
            new_goal_field.type = self.info.teams[player_info.team][player_info.id].info.goal_fields[new_location].type

            self.send(messages.Data(player_info.id, self.info.finished, {new_location: new_goal_field}, new_location))

        elif self.info.is_out_of_bounds(new_location):
            self.send(messages.Data(player_info.id, self.info.finished, player_location=player_info.location))

    def handle_discover_message(self, discover_message):

        sleep(float(self.discover_delay) / 1000)

        root = ET.fromstring(discover_message)
        player_id = root.attrib.get('playerId')
        player_info = self.find_player_by_id(player_id)

        goal_fields = {}
        task_fields = {}
        pieces = {}

        # get all 8 neighbours
        for (x, y), neighbour in player_info.info.get_neighbours(player_info.location, True).items():

            # if neighbour is a TaskField, update info about a player who is standing on that Field, and about distance to piece
            if self.info.is_task_field((x, y)):
                player_info.task_fields[x, y].player_id = neighbour.player_id
                player_info.task_fields[x, y].distance_to_piece = neighbour.distance_to_piece

                # if this field has a piece, check if player knows about it
                if neighbour.has_piece():
                    if neighbour.piece_id not in player_info.pieces.keys():
                        # if he doesn't know, add it to his dict
                        player_info.pieces[neighbour.piece_id] = PieceInfo(neighbour.piece_id,
                                                                           piece_type=PieceType.UNKNOWN.value)
                    pieces = player_info.pieces
                    player_info.task_fields[x, y].piece_id = neighbour.piece_id
                if len(pieces) < 1:
                    pieces = None
                task_fields[x, y] = player_info.task_fields[x, y]

            else:
                # it is a goal field.
                player_info.goal_fields[x, y].player_id = neighbour.player_id
                goal_fields[x, y] = player_info.goal_fields[x, y]

        self.send(messages.Data(player_id, self.info.finished, task_fields, goal_fields, pieces))

    def play(self):

        for team in self.info.teams.values():
            for player in team:
                self.send(messages.Game(player, self.info.teams, self.info.board_width, self.info.task_height,
                                        self.info.goals_height, team[player].location))

        Thread(target=self.place_pieces).start()

        while self.game_on:

            message = self.receive()
            if message is None:
                raise ConnectionAbortedError

            # handling depends on type of message:

            if "Move" in message:
                Thread(target=self.handle_move_message, args=message, daemon=True).start()

            elif "Discover" in message:
                Thread(target=self.handle_discover_message, args=message, daemon=True).start()

                # TODO: other types of messages:

    def get_num_of_players(self):
        return len(self.info.teams[Allegiance.BLUE.value]) + len(self.info.teams[Allegiance.RED.value])


if __name__ == '__main__':
    def simulate(verbose):
        gm = GameMaster(verbose)
        if gm.connect():
            gm.run()
            gm.shutdown()


    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    args = vars(parser.parse_args())
    simulate(args["verbose"])
