#!/usr/bin/env python
import random
import xml.etree.ElementTree as ET
from argparse import ArgumentParser

from src.communication import messages
from src.communication.client import Client, ClientTypeTag

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
        #  self.info = GameInfo()
        self.open_games = []
        self.game_name = game_name

    def play(self):
        self.send(messages.get_games())
        games = self.receive()
        self.open_games = parse_games(games)

        if len(self.open_games) > 0:
            self.send(messages.join_game(self.open_games[0][0], 'leader', 'red'))
            print("trying to join game :" + str(self.open_games[0][0]))
            confirmation = self.receive()
            print(confirmation)


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
