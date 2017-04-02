#!/usr/bin/env python
from argparse import ArgumentParser

from src.communication import messages
from src.communication.client import Client, ClientTypeTag
from src.communication.gameinfo import GameInfo
import xml.etree.ElementTree as ET
import random

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


def get_a_random_game(open_games):
    number_of_games = len(open_games)
    if number_of_games == 1:
        return open_games[0]

    random_index = random.randrange(start=0, stop=number_of_games - 1)
    return open_games[random_index]


class Player(Client):
    def __init__(self, index = 1, verbose = False):
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.PLAYER
        #  self.info = GameInfo()
        self.open_games = []
        self.messages_class = messages

    def play(self):
        self.send(messages.getgames())
        games = self.receive()
        self.open_games = parse_games(games)

        if len(self.open_games) > 0:
            random_game = get_a_random_game(self.open_games)
            self.send(self.messages_class.joingame(random_game[0], 'leader', 'red'))
            confirmation = self.receive()
            print(confirmation)


if __name__ == '__main__':
    def simulate(player_count, verbose):
        for i in range(player_count):
            p = Player(index = i, verbose = verbose)
            if p.connect():
                p.play()
                p.shutdown()


    parser = ArgumentParser()
    parser.add_argument('-c', '--playercount', default = 1, help = 'Number of players to be deployed.')
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Use verbose debugging mode.')
    args = vars(parser.parse_args())
    simulate(int(args["playercount"]), args["verbose"])
