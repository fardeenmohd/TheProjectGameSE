import os
import uuid
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from random import random, randint
from threading import Thread
from time import sleep

from src.communication import messages_old, messages_new
from src.communication.client import Client
from src.communication.info import GameInfo, GoalFieldInfo, Allegiance, TaskFieldInfo, PieceInfo, PieceType, \
    GoalFieldType, ClientTypeTag, PlayerRole
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
                             goals_height=goal_area_length)

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

        self.teams = {Allegiance.BLUE.value: {},
                      Allegiance.RED.value: {}}  # A dict of dicts: team => {player_id => role}
        self.red_players_locations = {}
        self.blue_players_locations = {}
        self.all_players = {} # id=>GameInfo

        self.parse_game_definition()
        self.parse_action_costs()

    def run(self):
        register_game_message = messages_new.register_game(self.game_name, self.team_limit,
                                                           self.team_limit)
        self.send(register_game_message)

        message = self.receive()

        try:
            if "RejectGameRegistration" in message:
                sleep(self.retry_register_game_interval)
                self.send(register_game_message)

            elif "ConfirmGameRegistration" in message:
                # read game id from message
                confirmation_root = ET.fromstring(message)
                self.info.id = int(confirmation_root.attrib.get("gameId"))

                while True:
                    # now, we will be receiving messages about players who are trying to join:
                    message = self.receive()  # this will block

                    if "JoinGame" in message:
                        self.handle_join(message)

                        if self.get_num_of_players() == self.team_limit * 2:
                            #  We are ready to start the game
                            self.send(messages_new.game_started(self.info.id))
                            self.set_up_game()
                            self.game_on = True
                            self.play()

                    else:
                        raise UnexpectedServerMessage

        except UnexpectedServerMessage:
            self.verbose_debug("Shutting down due to unexpected message: " + message)
            self.shutdown()

    def handle_join(self, message):
        # a player is trying to join! let's parse his message
        joingame_root = ET.fromstring(message)

        in_player_id = joingame_root.attrib.get("playerId")
        in_game_name = joingame_root.attrib.get("gameName")
        in_pref_team = joingame_root.attrib.get("preferedTeam")
        if in_pref_team == "red":
            in_pref_team = Allegiance.RED.value
        else:
            in_pref_team = Allegiance.BLUE.value
        in_pref_role = joingame_root.attrib.get("preferedRole")

        # in theory, received gamename has to be the same as our game, it should be impossible otherwise
        self.verbose_debug("A player is trying to join, with id: " + in_game_name + ".")
        if in_game_name != self.game_name:
            self.verbose_debug("The server somehow sent us a message with the wrong game name.")
            raise UnexpectedServerMessage

        # let's see if we can fit the player at all:
        if self.get_num_of_players() == self.team_limit * 2:
            # he can't fit in, send a rejection message :(
            self.verbose_debug("Player " + in_player_id + " was rejected, because the game is already full.")
            self.send(messages_new.reject_joining_game(in_player_id, self.game_name))
            return False

        # generating the private GUID
        private_guid = str(uuid.uuid4())

        # add him to a team while taking into account his preferences:
        team_color, role = self.add_player(in_player_id, in_pref_role, in_pref_team)

        self.verbose_debug("Player with id " + in_player_id + " was accepted to game, assigned role of " + role
                           + " in team " + team_color + ".")

        self.send(
            messages_new.confirm_joining_game(str(in_player_id), str(self.info.id), private_guid, team_color, role))

    def set_up_game(self):
        # now that the players have connected, we can prepare the game
        whole_board_length = 2 * self.info.goals_height + self.info.task_height - 1

        # initialize goal and task fields:
        y = whole_board_length

        for i in range(self.info.goals_height):
            for x in range(self.info.board_width):
                if (x, y) not in self.info.goal_fields.keys():
                    self.info.goal_fields[x, y] = GoalFieldInfo(x, y, Allegiance.RED.value)
            y -= 1

        for i in range(self.info.task_height):
            for x in range(self.info.board_width):
                self.info.task_fields[x, y] = TaskFieldInfo(x, y)
            y -= 1

        for i in range(self.info.goals_height):
            for x in range(self.info.board_width):
                if (x, y) not in self.info.goal_fields.keys():
                    self.info.goal_fields[x, y] = GoalFieldInfo(x, y, Allegiance.BLUE.value)
            y -= 1

        # place the players:
        for i in self.teams[Allegiance.RED.value].keys():
            x = randint(0, self.info.board_width - 1)
            y = randint(0, self.info.goals_height - 1)
            random_red_goal_field = self.info.goal_fields[x, y]
            while not random_red_goal_field.is_occupied() and random_red_goal_field.type is GoalFieldType.NON_GOAL:
                x = randint(0, self.info.board_width - 1)
                y = randint(0, self.info.goals_height)
                random_red_goal_field = self.info.goal_fields[x, y]

            self.info.goal_fields[x, y].player_id = int(i)
            self.red_players_locations[i] = (x, y)

        for i in self.teams[Allegiance.BLUE.value].keys():
            x = randint(0, self.info.board_width - 1)
            y = randint(whole_board_length - self.info.goals_height + 1, whole_board_length)
            random_blue_goal_field = self.info.goal_fields[x, y]
            while not random_blue_goal_field.is_occupied() and random_blue_goal_field.type is GoalFieldType.NON_GOAL:
                x = randint(self.info.board_width - 1)
                y = randint(whole_board_length - self.info.goals_height + 1, whole_board_length)
                random_blue_goal_field = self.info.goal_fields[x, y]

            self.info.goal_fields[x, y].player_id = int(i)
            self.blue_players_locations[i] = (x, y)

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

        x = randint(0, self.info.board_width - 1)
        y = randint(0, self.info.task_height - 1)

        i = 0
        while self.info.has_piece(x, y) and i < self.RANDOMIZATION_ATTEMPTS:
            x = randint(0, self.info.board_width - 1)
            y = randint(0, self.info.task_height - 1)
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

        self.info.task_fields[x, y].piece_id = piece_id
        self.info.pieces[piece_id] = new_piece
        self.piece_indexer += 1
        self.verbose_debug(
            "Added a " + new_piece.piece_type + " piece with id: " + piece_id + "at coordinates " + str(x) + ", " + str(
                y) + ".")

    def add_player(self, player_id, pref_role, pref_team):
        """
        :returns: a tuple: (team, role)
        """
        team = ""
        role = ""

        if len(self.teams[pref_team]) == self.team_limit:
            if pref_team == Allegiance.BLUE.value:
                team = Allegiance.RED.value
            else:
                team = Allegiance.BLUE.value
        else:
            team = pref_team

        if pref_role == PlayerRole.LEADER.value:
            for player in self.teams[team].values():
                if player == PlayerRole.LEADER.value:
                    role = PlayerRole.MEMBER.value
                else:
                    role = PlayerRole.LEADER.value
        else:
            role = PlayerRole.MEMBER.value

        self.teams[team][player_id] = role
        return team, role

    def play(self):
        for team in self.teams.keys():
            for player_id in self.teams[team]:
                self.all_players[player_id] = GameInfo()
                if team is Allegiance.BLUE.value:
                    self.send(messages_new.game(player_id, self.teams, self.info.board_width,
                                                self.info.task_height, self.info.goals_height,
                                                self.blue_players_locations[player_id]))
                    sleep(1)
                else:
                    self.send(messages_new.game(player_id, self.teams, self.info.board_width,
                                                self.info.task_height, self.info.goals_height,
                                                self.red_players_locations[player_id]))
                    sleep(1)
        Thread(target=self.place_pieces(), daemon=True).start()

        while self.game_on:
            message = self.receive()

        self.send("Thanks for the message.")

    def get_num_of_players(self):
        return len(self.teams[Allegiance.BLUE.value]) + len(self.teams[Allegiance.RED.value])


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
