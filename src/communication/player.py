#!/usr/bin/env python
import random
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from src.communication import messages
from src.communication.client import Client, ClientTypeTag
from src.communication.info import GameInfo, GoalFieldInfo, Allegiance, TaskFieldInfo, PieceInfo, PieceType, \
    GoalFieldType

REGISTERED_GAMES_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"


def parse_games(games):
    open_games = []
    root = ET.fromstring(games)

    for registered_games in root.findall(REGISTERED_GAMES_TAG + "GameInfo"):
        game_name = registered_games.get("gameName")
        blue_team_players = int(registered_games.get("blueTeamPlayers"))
        red_team_players = int(registered_games.get("redTeamPlayers"))
        open_games.append((game_name, blue_team_players, red_team_players))

    return open_games


class Player(Client):
    def __init__(self, index=1, verbose=False, game_name='InitialGame'):
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.PLAYER
        self.Guid = 'Not Assigned'
        self.game_info = GameInfo()
        self.open_games = []
        self.game_name = game_name
        self.team = 'Not Assigned'
        self.role = 'Not Assigned'
        self.location = {}
        self.all_players = []
        self.blue_player_list = []
        self.red_player_list = []

    def confirmation_status_handling(self, confirmation_message):
        if "ConfirmJoiningGame" in confirmation_message:
            root = ET.fromstring(confirmation_message)
            self.Guid = root.attrib.get('privateGuid')
            self.game_info.id = int(root.attrib.get('gameId'))
            self.game_info.name = self.game_name

            for player_definition in root.findall(REGISTERED_GAMES_TAG + "PlayerDefinition"):
                self.team = player_definition.attrib.get('team')
                self.role = player_definition.attrib.get('type')

            return True
        else:
            print("Got rejected by the server so shutting down")
            self.shutdown()
            return False

    def game_message_handling(self, game_message):
        root = ET.fromstring(game_message)

        for board in root.findall(REGISTERED_GAMES_TAG + "Board"):
            self.game_info.task_height = board.attrib.get('tasksHeight')
            self.game_info.board_width = board.attrib.get('width')
            self.game_info.goals_height = board.attrib.get('goalsHeight')

        for player_location in root.findall(REGISTERED_GAMES_TAG + "PlayerLocation"):
            self.location['x'] = player_location.attrib.get('x')
            self.location['y'] = player_location.attrib.get('y')
        print(self.location)
        red_player_count = 0
        blue_player_count = 0
        for player_list in root.findall(REGISTERED_GAMES_TAG + "Players"):
            for player in player_list.findall(REGISTERED_GAMES_TAG + "Player"):
                self.all_players.append(
                    (player.attrib.get('team'), player.attrib.get('type'), int(player.attrib.get('id'))))

                if player.attrib.get('team') == 'blue':
                    self.blue_player_list.append(
                        (player.attrib.get('team'), player.attrib.get('type'), int(player.attrib.get('id'))))
                    self.game_info.blue_player_list[player.attrib.get('id')] = player.attrib.get('type')
                    blue_player_count += 1

                if player.attrib.get('team') == 'red':
                    self.red_player_list.append(
                        (player.attrib.get('team'), player.attrib.get('type'), int(player.attrib.get('id'))))
                    self.game_info.red_player_list[player.attrib.get('id')] = player.attrib.get('type')
                    red_player_count += 1

        self.game_info.red_players = red_player_count
        self.game_info.blue_players = blue_player_count

    def play(self):
        self.send(messages.get_games())
        games = self.receive()

        if 'RegisteredGames' in games:
            self.open_games = parse_games(games)

            if len(self.open_games) > 0:
                temp_game_name = self.open_games[0][0]
                temp_preferred_role = 'leader'
                temp_preferred_team = 'red'
                self.send(messages.join_game(temp_game_name, temp_preferred_role, temp_preferred_team))
                confirmation = self.receive()
                if confirmation is not None:
                    self.confirmation_status_handling(confirmation)
                game_info = self.receive()
                if game_info is not None:
                    self.game_message_handling(game_info)


if __name__ == '__main__':
    def simulate(player_count, verbose):
        game_name = 'InitialGame'
        for i in range(player_count):
            p = Player(index=i, verbose=verbose, game_name=game_name)
            if p.connect():
                p.play()
                p.shutdown()


    parser = ArgumentParser()
    parser.add_argument('-c', '--playercount', default=1, help='Number of players to be deployed.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    args = vars(parser.parse_args())
    simulate(int(args["playercount"]), args["verbose"])
