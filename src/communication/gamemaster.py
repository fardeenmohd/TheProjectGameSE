from src.communication.client import Client, ClientTypeTag
from src.communication.gameinfo import GameInfo, GoalFieldInfo, Allegiance, TaskFieldInfo, PieceInfo, PieceType
from src.communication import messages
from src.communication.unexpected import UnexpectedServerMessage
import os
import xml.etree.ElementTree as ET
import argparse
import random
import time
import threading
import datetime


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

        goals = []

        board_width = 0
        task_area_length = 0
        goal_area_length = 0

        for game_attributes in root.findall(GAME_SETTINGS_TAG + "GameDefinition"):
            # load goal field information:
            for goal in game_attributes.findall(GAME_SETTINGS_TAG + "Goals"):
                colour = goal.get("team")
                x = int(goal.get("x"))
                y = int(goal.get("y"))
                if colour == "red":
                    goals.append(GoalFieldInfo(x, y, Allegiance.RED))
                if colour == "blue":
                    goals.append(GoalFieldInfo(x, y, Allegiance.BLUE))

            self.sham_probability = float(game_attributes.find(GAME_SETTINGS_TAG + "ShamProbability").text)
            self.placing_pieces_frequency = int(
                game_attributes.find(GAME_SETTINGS_TAG + "PlacingNewPiecesFrequency").text)
            self.initial_number_of_pieces = int(game_attributes.find(GAME_SETTINGS_TAG + "InitialNumberOfPieces").text)
            board_width = int(game_attributes.find(GAME_SETTINGS_TAG + "BoardWidth").text)
            task_area_length = int(game_attributes.find(GAME_SETTINGS_TAG + "TaskAreaLength").text)
            goal_area_length = int(game_attributes.find(GAME_SETTINGS_TAG + "GoalAreaLength").text)
            self.game_name = game_attributes.find(GAME_SETTINGS_TAG + "GameName").text
            self.number_of_players_per_team = int(
                game_attributes.find(GAME_SETTINGS_TAG + "NumberOfPlayersPerTeam").text)

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

    def __init__(self, index=1, verbose=False):
        super().__init__(index, verbose)

        self.RANDOMIZATION_ATTEMPTS = 10
        self.piece_counter = 0
        self.typeTag = ClientTypeTag.GAMEMASTER
        self.game_on = False

        self.parse_game_definition()
        self.parse_action_costs()

    def run(self):
        register_game_message = messages.registergame(self.game_name, redplayers=self.number_of_players_per_team,
                                                      blueplayers=self.number_of_players_per_team)
        self.send(register_game_message)

        message = self.receive()

        try:
            if "RejectGameRegistration" in message:
                time.sleep(self.retry_register_game_interval)
                self.send(register_game_message)

            elif "ConfirmGameRegistration" in message:
                # read game id from message
                confirmation_root = ET.fromstring(message)
                self.info.id = int(confirmation_root.attrib.get("gameId"))

                # now, wait until we receive information that the game hath begun.
                message = self.receive()  # this will block

                if "GameStarted" in message:
                    # good, the game has started.
                    start_root = ET.fromstring(message)
                    if self.info.id != int(start_root.attrib.get("gameId")):
                        raise UnexpectedServerMessage

                    else:
                        # the game starts:
                        self.game()

                else:
                    raise UnexpectedServerMessage

            else:
                raise UnexpectedServerMessage

        except UnexpectedServerMessage:
            self.verbose_debug("Shutting down due to unexpected message: " + message)
            self.shutdown()

    def game(self):
        # the actual game begins

        # create the first pieces:
        for i in range(self.initial_number_of_pieces):
            self.add_piece()

        threading.Thread(target=self.add_piece(), daemon=True).start()

        self.game_on = True

        while self.game_on:
            message = self.receive()
            self.send("Thanks for the message.")

    def add_piece(self):
        id = self.piece_counter

        # check if we can add the piece at all:
        if not self.info.check_for_empty_fields():
            return False

        x = random.randint(0, self.info.board_width)
        y = random.randint(0, self.info.task_height)

        i = 0
        while self.info.has_piece(x, y) and i < self.RANDOMIZATION_ATTEMPTS:
            x = random.randint(0, self.info.board_width)
            y = random.randint(0, self.info.task_height)

        if self.info.has_piece(x, y):
            for task_field in self.info.task_fields:
                if not task_field.has_piece():
                    x = task_field.x
                    y = task_field.y

        field = TaskFieldInfo(x, y, datetime.datetime.now(), 0, -1, id)
        new_piece = PieceInfo(id, datetime.datetime.now())

        if random() >= self.sham_probability:
            new_piece.piece_type = PieceType.LEGIT
        else:
            new_piece.piece_type = PieceType.SHAM

        self.info.task_fields[x, y] = field
        self.info.pieces[id] = new_piece

    def place_pieces(self):
        while self.game_on:
            time.sleep(float(self.placing_pieces_frequency) / 1000)
            self.add_piece()


if __name__ == '__main__':
    def simulate(gamemaster_count, verbose):
        for i in range(gamemaster_count):
            gm = GameMaster(i, verbose)
            if gm.connect():
                gm.run()
                gm.shutdown()


    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--gamemastercount', default=1, help='Number of gamemasters to be deployed.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    args = vars(parser.parse_args())
    simulate(int(args["gamemastercount"]), args["verbose"])
