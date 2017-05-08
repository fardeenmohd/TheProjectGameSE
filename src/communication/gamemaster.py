import copy
import os
import uuid
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from random import random, randint
from threading import Thread
from time import sleep

from src.communication import messages
from src.communication.client import Client
from src.communication.info import GameInfo, Direction, Allegiance, PieceInfo, PieceType, \
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

        self.goals = []  # list of tuples ;)

        board_width = 0
        task_area_length = 0
        goal_area_length = 0

        for game_attributes in root.findall(GAME_SETTINGS_TAG + "GameDefinition"):
            # load goal field information:
            for goal in game_attributes.findall(GAME_SETTINGS_TAG + "Goals"):
                colour = goal.get("team")
                x = int(goal.get("x"))
                y = int(goal.get("y"))
                self.goals.append((x, y))

            self.sham_probability = float(game_attributes.find(GAME_SETTINGS_TAG + "ShamProbability").text)
            self.placing_pieces_frequency = int(
                game_attributes.find(GAME_SETTINGS_TAG + "PlacingNewPiecesFrequency").text)
            self.initial_number_of_pieces = int(game_attributes.find(GAME_SETTINGS_TAG + "InitialNumberOfPieces").text)
            board_width = int(game_attributes.find(GAME_SETTINGS_TAG + "BoardWidth").text)
            task_area_length = int(game_attributes.find(GAME_SETTINGS_TAG + "TaskAreaLength").text)
            goal_area_length = int(game_attributes.find(GAME_SETTINGS_TAG + "GoalAreaLength").text)

            self.game_name = game_attributes.find(GAME_SETTINGS_TAG + "GameName").text
            self.team_limit = int(game_attributes.find(GAME_SETTINGS_TAG + "NumberOfPlayersPerTeam").text)

        self.info = GameInfo(board_width=board_width, task_height=task_area_length,
                             goals_height=goal_area_length, max_blue_players=self.team_limit,
                             max_red_players=self.team_limit)

        self.goal_target = len(self.goals) / 2

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

        self.achieved_goal_counters = {Allegiance.RED.value: 0, Allegiance.BLUE.value: 0}

        self.PIECE_DICT_PRELOAD_CAPACITY = 256
        self.RANDOMIZATION_ATTEMPTS = 10
        self.typeTag = ClientTypeTag.GAME_MASTER
        self.game_on = False
        self.piece_indexer = 0
        self.num_occupied_red_goals = 0
        self.num_occupied_blue_goals = 0
        self.parse_game_definition()
        self.parse_action_costs()
        self.piece_placer = Thread()

    @property
    def get_num_of_players(self):
        return len(self.info.teams[Allegiance.BLUE.value]) + len(self.info.teams[Allegiance.RED.value])

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

                        if self.get_num_of_players == self.team_limit * 2:
                            #  We are ready to start the game
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
        if self.get_num_of_players == self.team_limit * 2:
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
        return True

    def set_up_game(self):
        # now that the players have connected, we can prepare the game
        self.info.initialize_fields()

        # set-up the goal fields using info obtained from the configuration file:
        for goal_field in self.info.goal_fields.values():
            if goal_field.location in self.goals:
                goal_field.type = GoalFieldType.GOAL.value
            else:
                goal_field.type = GoalFieldType.NON_GOAL.value

        # place the players:
        # red team:
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

        # blue team:
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
        for i in range(self.PIECE_DICT_PRELOAD_CAPACITY):
            # using pre-loading of the dict to avoid thread synchronization problems due to changing size of dict
            if i <= self.initial_number_of_pieces:
                self.add_piece()
            else:
                self.info.pieces[str(i)] = PieceInfo()

    def place_pieces(self):
        # this function runs on a thread and keeps adding new pieces to the board. forever.
        while self.game_on:
            sleep(float(self.placing_pieces_frequency) / 1000)
            self.add_piece()

    def add_piece(self):
        """
        randomly place a piece on the board (if possible)
        """
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
            for task_field in self.info.task_fields.values():
                if not task_field.has_piece:
                    x = task_field.x
                    y = task_field.y
                    break

        new_piece = PieceInfo(piece_id, location=(x, y))

        # assign type to new piece
        if random() >= self.sham_probability:
            new_piece.type = PieceType.NORMAL.value
        else:
            new_piece.type = PieceType.SHAM.value

        self.info.task_fields[x, y].piece_id = piece_id
        self.info.pieces[piece_id] = new_piece

        # update distance_to_piece in all fields:
        self.info.update_field_distances()

        self.piece_indexer += 1
        self.verbose_debug(
            "Added a " + new_piece.type + " piece with id: " + piece_id + " at coordinates " + str(x) + ", " + str(
                y) + ".")

    def add_player(self, player_id, pref_role, pref_team, private_guid):
        """
        adds the player to game while taking into account his preferences
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

        # add this player to our dict of teams, set up his game info.
        self.info.teams[team][player_id] = PlayerInfo(player_id, team, type=role, guid=private_guid)
        self.info.teams[team][player_id].info.initialize_fields(self.info.goals_height, self.info.task_height,
                                                                self.info.board_width)
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

    def handle_move_message(self, direction, player_info: PlayerInfo):

        sleep(float(self.move_delay) / 1000)

        new_location = player_info.location

        if direction == Direction.UP.value:
            new_location = player_info.location[0], player_info.location[1] + 1

        if direction == Direction.DOWN.value:
            new_location = player_info.location[0], player_info.location[1] - 1

        if direction == Direction.LEFT.value:
            new_location = player_info.location[0] - 1, player_info.location[1]

        if direction == Direction.RIGHT.value:
            new_location = player_info.location[0] + 1, player_info.location[1]

        old_location = player_info.location
        if self.info.is_task_field(old_location):
            old_field = self.info.task_fields[old_location]
        else:
            old_field = self.info.goal_fields[old_location]
        player_info.location = new_location

        if self.info.is_task_field(new_location):
            new_task_field = self.info.task_fields[new_location]

            if new_task_field.is_occupied:
                # can't move, stay in the same location.
                player_info.location = old_location
                old_field.player_id = player_info.id
                self.send(messages.Data(player_info.id, self.info.finished,player_location=player_info.location,task_fields={new_location :new_task_field}))

            else:
                # we can move to the new field.
                new_task_field.player_id = player_info.id
                old_field.player_id = "-1"  # set old field to not have a player.

                if new_task_field.has_piece:
                    piece_id = new_task_field.piece_id

                    # check if the Player already knows what type this piece is:
                    # if yes, keep his information about it:
                    piece_info = player_info.info.pieces.get(piece_id)

                    if piece_info is None:
                        # if he doesn't yet know about the Piece, set its type to unknown
                        piece_info = PieceInfo(piece_id, type=PieceType.UNKNOWN.value, location=new_location)
                        player_info.info.pieces[piece_id] = piece_info

                    piece_dict = {piece_id: piece_info}

                    # finally, send the message.
                    self.send(
                        messages.Data(player_info.id, self.info.finished, task_fields={new_location: new_task_field},
                                      pieces=piece_dict, player_location=new_location))
                else:
                    # this new field doesn't have a piece.
                    self.send(messages.Data(player_info.id, self.info.finished,
                                            task_fields={new_location: new_task_field}, player_location=new_location))

        elif self.info.is_goal_field(new_location):
            # it's a Goal Field, yo.
            if self.info.goal_fields[new_location].allegiance != player_info.team:
                player_info.location = old_location
                self.send(messages.Data(player_info.id, self.info.finished,player_location=player_info.location ))

            # i.e. a Red player shouldn't be allowed to enter a Blue goals area and vice versa.

            if self.info.goal_fields[new_location].is_occupied:
                # can't move.
                player_info.location = old_location
                self.send(messages.Data(player_info.id, self.info.finished,goal_fields={new_location : self.info.goal_fields[new_location]}, player_location=player_info.location))

            else:
                # get a working copy of the new field.
                new_goal_field = copy.deepcopy(self.info.goal_fields[new_location])
                # use the type that the player knows.
                new_goal_field.type = player_info.info.goal_fields[new_location].type

                self.info.goal_fields[new_location].player_id = player_info.id
                old_field.player_id = "-1"  # set old field to not have a player.

                self.send(messages.Data(player_info.id, self.info.finished, goal_fields={new_location: new_goal_field},
                                        player_location=player_info.location))

        elif self.info.is_out_of_bounds(new_location):
            player_info.location = old_location
            self.send(messages.Data(player_info.id, self.info.finished, player_location=player_info.location))

    def handle_discover_message(self, player_info: PlayerInfo):

        sleep(float(self.discover_delay) / 1000)

        goal_fields = {}
        task_fields = {}
        pieces = {}

        # get all 8 neighbours
        for (x, y), neighbour in self.info.get_neighbours(player_info.location, True).items():

            # if neighbour is a TaskField, update info about a player who is standing on that Field, and about distance to piece
            if self.info.is_task_field((x, y)):
                player_info.info.task_fields[x, y].player_id = neighbour.player_id
                player_info.info.task_fields[x, y].distance_to_piece = neighbour.distance_to_piece

                if neighbour.has_piece:
                    # if this field has a piece, check if player knows about it
                    if neighbour.piece_id not in player_info.info.pieces.keys():
                        # if he doesn't know, add an unknown piece to his info
                        player_info.info.pieces[neighbour.piece_id] = PieceInfo(neighbour.piece_id,
                                                                                location=neighbour.location)
                    player_info.info.task_fields[x, y].piece_id = neighbour.piece_id

                    pieces[neighbour.piece_id] = player_info.info.pieces[neighbour.piece_id]
                task_fields[x, y] = player_info.info.task_fields[x, y]

            else:
                # it is a goal field.
                # get a working copy of the new field.
                new_goal_field = copy.deepcopy(self.info.goal_fields[neighbour.location])
                # use the type that the player knows.
                new_goal_field.type = player_info.info.goal_fields[neighbour.location].type

                player_info.info.goal_fields[x, y] = new_goal_field
                goal_fields[x, y] = player_info.info.goal_fields[x, y]

        # add information about the player's own field:
        if self.info.is_goal_field(player_info.location):
            # get a working copy of the new field.
            new_goal_field = copy.deepcopy(self.info.goal_fields[player_info.location])
            # use the type that the player knows.
            new_goal_field.type = player_info.info.goal_fields[player_info.location].type

            player_info.info.goal_fields[player_info.location] = new_goal_field
            goal_fields[player_info.location] = player_info.info.goal_fields[player_info.location]
        else:
            # it's a task field...
            field = player_info.info.task_fields[player_info.location]
            field.distance_to_piece = self.info.task_fields[player_info.location].distance_to_piece

            if self.info.task_fields[player_info.location].has_piece:
                # if this field has a piece, check if player knows about it
                piece_id = self.info.task_fields[player_info.location].piece_id
                if piece_id not in player_info.info.pieces.keys():
                    # if he doesn't know, add an unknown piece to his info
                    player_info.info.pieces[piece_id] = PieceInfo(piece_id, location=player_info.location)
                player_info.info.task_fields[player_info.location].piece_id = piece_id

                pieces[piece_id] = player_info.info.pieces[piece_id]
            task_fields[player_info.location] = player_info.info.task_fields[player_info.location]

        if len(pieces) < 1:
            pieces = None
        if len(goal_fields) < 1:
            goal_fields = None
        if len(task_fields) < 1:
            task_fields = None

        self.send(messages.Data(player_info.id, self.info.finished, task_fields, goal_fields, pieces))

    def handle_pick_up_message(self, player_info: PlayerInfo):

        sleep(float(self.pickup_delay) / 1000)

        location = player_info.location

        # check if the field is a task field:
        if self.info.is_task_field(location):
            # then check if there is a piece on this field:
            if self.info.has_piece(location[0], location[1]):
                # update GM's knowledge:
                piece_id = self.info.task_fields[location].piece_id
                self.info.pieces[piece_id].player_id = player_info.id
                self.info.task_fields[location].piece_id = "-1"  # setting as empty

                # we update the GM's info of distance to pieces so it sends valid data later to player
                self.info.update_field_distances()

                player_info.piece_id = piece_id

                # update player's knowledge:
                players_piece_info = player_info.info.pieces.get(piece_id)
                if players_piece_info is not None:
                    players_piece_info.player_id = player_info.id
                    players_piece_info.location = None  # set to None to indicate that it was picked up.
                else:
                    players_piece_info = PieceInfo(piece_id, PieceType.UNKNOWN.value, player_info.id)
                    player_info.info.pieces[piece_id] = players_piece_info
                players_piece_info.piece_id = "-1"

                # send him piece Data with his info about the piece
                self.send(messages.Data(player_info.id, self.info.finished, pieces={piece_id: players_piece_info}))

            else:
                # no piece on this field. respond with an empty Data message
                self.send(messages.Data(player_info.id, self.info.finished))
        else:
            # piece isn't a task field, there can be no pieces on it to pick up, respond with an empty Data message
            self.send(messages.Data(player_info.id, self.info.finished))

    def handle_place_message(self, player_info: PlayerInfo):

        sleep(float(self.placing_delay) / 1000)

        # check if that player really has a piece:
        piece_id = player_info.piece_id
        if piece_id == "-1" or piece_id is None:
            # seems like the player doesn't have a piece at all. send him an empty Data message
            self.send(messages.Data(player_info.id, self.info.finished))

        else:
            # check if the player is standing on TaskField or GoalField:
            if self.info.is_task_field(player_info.location):
                # update GM's info
                self.info.task_fields[player_info.location].piece_id = piece_id
                self.info.pieces[piece_id].location = player_info.location
                self.info.pieces[piece_id].player_id = "-1"  # mark as untaken.

                # update player's info
                player_info.info.task_fields[player_info.location].piece_id = piece_id
                player_info.info.pieces[piece_id].player_id = "-1"  # untaken
                player_info.info.pieces[piece_id].location = player_info.location

                field = player_info.info.task_fields[player_info.location]

                # send him a response
                self.send(messages.Data(player_info.id, self.info.finished, task_fields={field.location: field}))

            else:
                # the field is a goal field.

                # warning: this piece will be consumed and never again picked up.
                # as such it should probably be deleted from the dict of all pieces.
                # however, i want to avoid thread synchronization problems that could occur due to changing the size of a dict during runtime
                # hence i set the owner of a piece to -1 and its location to None :)

                # update GM's info:
                self.info.pieces[piece_id].player_id = "-1"
                self.info.pieces[piece_id].location = None

                # update player info.
                player_info.piece_id = "-1"  # he holds nothing.
                player_info.info.pieces[piece_id].player_id = "-1"
                player_info.info.pieces[piece_id].location = None

                # check if the piece is legit:
                if self.info.pieces[piece_id].type == PieceType.NORMAL.value:

                    # update player info about this field
                    field = self.info.goal_fields[player_info.location]
                    player_info.info.goal_fields[player_info.location].type = field.type

                    if field.type == GoalFieldType.GOAL.value:
                        self.achieved_goal_counters[player_info.team] += 1

                    # player is placing a piece in a goal field so we check for game over
                    self.check_for_game_over(player_info)

                    # send information about the true nature of this goal field
                    self.send(messages.Data(player_info.id, self.info.finished, goal_fields={field.location: field}))

                else:
                    # piece is a sham, send an empty Data message
                    self.send(messages.Data(player_info.id, self.info.finished))

    def check_for_game_over(self, player_info: PlayerInfo):
        # update self.info.finished and self.game_on if a team has completed all its goals.

        for team in self.info.teams.keys():
            if self.achieved_goal_counters[team] >= self.goal_target:
                self.verbose_debug(team.upper() + " TEAM HAS WON THE GAME!\nWe shall be restarting the game in:.", True)
                self.piece_placer.join()
                self.info.finished = True
                print("5")
                sleep(1)
                print("4")
                sleep(1)
                print("3")
                sleep(1)
                print("2")
                sleep(1)
                print("1")
                sleep(1)
                self.game_on = False
                break

    def play(self):
        # send the initial Game message to all players:
        for team in self.info.teams.values():
            for player in team:
                self.send(messages.Game(player, self.info.teams, self.info.board_width, self.info.task_height,
                                        self.info.goals_height, team[player].location))

        self.send(messages.GameStarted(self.info.id))

        # deploy the Piece-placing thread:
        self.piece_placer =  Thread(target=self.place_pieces)
        self.piece_placer.start()

        while self.game_on:
            try:
                message = self.receive()
                if message is None:
                    raise ConnectionAbortedError

                # handling depends on type of message:
                root = ET.fromstring(message)

                player_guid = root.attrib.get("playerGuid")
                player_info = self.find_player_by_guid(player_guid)

                if "Move" in message:
                    direction = root.get('direction')
                    Thread(target=self.handle_move_message, args=[direction, player_info], daemon=True).start()

                elif "Discover" in message:
                    Thread(target=self.handle_discover_message, args=[player_info], daemon=True).start()

                elif "PlacePiece" in message:
                    Thread(target=self.handle_place_message, args=[player_info], daemon=True).start()

                elif "PickUpPiece" in message:
                    Thread(target=self.handle_pick_up_message, args=[player_info], daemon=True).start()

                    # TODO: add handling of other types of messages

            except Exception as e:
                self.verbose_debug("Is this an error I see before me? " + str(e), True)
                raise e

        if self.info.finished:
            self.clean_up()
            self.run()

    def clean_up(self):
        # clean up the info and prepare to start a new game
        self.achieved_goal_counters = {Allegiance.RED.value: 0, Allegiance.BLUE.value: 0}

        self.PIECE_DICT_PRELOAD_CAPACITY = 256
        self.RANDOMIZATION_ATTEMPTS = 10
        self.piece_indexer = 0
        self.game_on = False
        self.num_occupied_red_goals = 0
        self.num_occupied_blue_goals = 0
        self.parse_game_definition()
        self.parse_action_costs()
        self.piece_placer = Thread()

    def shutdown(self):
        super(GameMaster, self).shutdown()
        self.piece_placer.join()


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
