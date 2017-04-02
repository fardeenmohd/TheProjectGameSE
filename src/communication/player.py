#!/usr/bin/env python
from argparse import ArgumentParser

from communication import messages
from communication.client import Client, ClientTypeTag


class Player(Client):
    def __init__(self, index = 1, verbose = False):
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.PLAYER

    #  self.info = GameInfo()

    def play(self):
        self.send(messages.getgames())

        games = self.receive()


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
