from src.communication.client import Client, ClientTypeTag
from src.communication.gameinfo import GameInfo
from src.communication import messages
import os
import xml.etree.ElementTree as ET

GAME_SETTINGS_TAG = "{https://se2.mini.pw.edu.pl/17-pl-19/17-pl-19/}"


def parse_game_master_settings():
    full_file = os.getcwd() + "\GameMasterSettings.xml"
    tree = ET.parse(full_file)
    root = tree.getroot()

    return root


def get_game_definition():
    root = parse_game_master_settings()

    keep_alive_interval = int(root.attrib.get('KeepAliveInterval'))
    retry_register_game_interval = int(root.attrib.get('RetryRegisterGameInterval'))
    red_goals = []
    blue_goals = []
    sham_probability = 0
    placing_new_pieces_frequency = 0
    initial_number_of_pieces = 0
    board_width = 0
    task_area_length = 0
    goal_area_length = 0
    number_of_players_per_team = 0
    game_name = ''

    for game_attributes in root.findall(GAME_SETTINGS_TAG + "GameDefinition"):
        for Goals in game_attributes.findall(GAME_SETTINGS_TAG + "Goals"):
            colour = Goals.get("team")
            if colour == "red":
                x = int(Goals.get("x"))
                y = int(Goals.get("y"))
                red_goals.append((x, y))
            if colour == "blue":
                x = int(Goals.get("x"))
                y = int(Goals.get("y"))
                blue_goals.append((x, y))
        sham_probability = float(
            game_attributes.find(GAME_SETTINGS_TAG + "ShamProbability").text)
        placing_new_pieces_frequency = int(
            game_attributes.find(GAME_SETTINGS_TAG + "PlacingNewPiecesFrequency").text)
        initial_number_of_pieces = int(
            game_attributes.find(GAME_SETTINGS_TAG + "InitialNumberOfPieces").text)
        board_width = int(
            game_attributes.find(GAME_SETTINGS_TAG + "BoardWidth").text)
        task_area_length = int(
            game_attributes.find(GAME_SETTINGS_TAG + "TaskAreaLength").text)
        goal_area_length = int(
            game_attributes.find(GAME_SETTINGS_TAG + "GoalAreaLength").text)

        game_name = game_attributes.find(GAME_SETTINGS_TAG + "GameName").text
        number_of_players_per_team = int(
            game_attributes.find(GAME_SETTINGS_TAG + "NumberOfPlayersPerTeam").text)

    return [keep_alive_interval,
            retry_register_game_interval,
            red_goals,
            blue_goals,
            sham_probability,
            placing_new_pieces_frequency,
            initial_number_of_pieces,
            board_width,
            task_area_length,
            goal_area_length,
            number_of_players_per_team,
            game_name]


def get_action_costs():
    root = parse_game_master_settings()
    move_delay = 0
    discover_delay = 0
    test_delay = 0
    pickup_delay = 0
    placing_delay = 0
    knowledge_exchange_delay = 0

    for action_costs in root.findall(GAME_SETTINGS_TAG + "ActionCosts"):
        move_delay = int(
            action_costs.find(GAME_SETTINGS_TAG + "MoveDelay").text)
        discover_delay = int(
            action_costs.find(GAME_SETTINGS_TAG + "DiscoverDelay").text)
        test_delay = int(
            action_costs.find(GAME_SETTINGS_TAG + "TestDelay").text)
        pickup_delay = int(
            action_costs.find(GAME_SETTINGS_TAG + "PickUpDelay").text)
        placing_delay = int(
            action_costs.find(GAME_SETTINGS_TAG + "PlacingDelay").text)
        knowledge_exchange_delay = int(
            action_costs.find(GAME_SETTINGS_TAG + "KnowledgeExchangeDelay").text)

    return [move_delay,
            discover_delay,
            test_delay,
            pickup_delay,
            placing_delay,
            knowledge_exchange_delay]


class GameMaster(Client):
    def __init__(self, index=1, verbose=False):
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.GAMEMASTER

        [self.keep_alive_interval,
         self.retry_register_game_interval,
         self.red_goals,
         self.blue_goals,
         self.sham_probability,
         self.placing_new_pieces_frequency,
         self.initial_number_of_pieces,
         self.board_width,
         self.task_area_length,
         self.goal_area_length,
         self.number_of_players_per_team,
         self.game_name] = get_game_definition()

        [self.move_delay,
         self.discover_delay,
         self.test_delay,
         self.pickup_delay,
         self.placing_delay,
         self.knowledge_exchange_delay] = get_action_costs()

        #self.info = GameInfo()
        self.messages_class = messages.Message()

    def run(self):
        self.send(self.messages_class.registergame(gamename=self.game_name, redplayers=self.number_of_players_per_team,
                                                   blueplayers=self.number_of_players_per_team))
        self.talk(5)


if __name__ == '__main__':
    # parser = ArgumentParser()
    # parser.add_argument('-c', '--gamemastercount', default = 1, help = 'Number of gamemasters to be deployed.')
    # parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Use verbose debugging mode.')
    # args = vars(parser.parse_args())
    # simulate(int(args["gamemastercount"]), args["verbose"]))
    gm = GameMaster(verbose=True)
    gm.connect()
    gm.run()
    gm.shutdown()
