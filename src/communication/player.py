#!/usr/bin/env python

from src.communication import messages
from src.communication.client import Client, ClientTypeTag
from src.communication.gameinfo import GameInfo


class Player(Client):
    def __init__(self, index=1, verbose=False):
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.PLAYER
        #  self.info = GameInfo()

    def play(self):
        self.send(messages.getgames())
        self.talk(5)

    # TODO: parse games: check what's open, try to join :)

if __name__ == '__main__':
    # parser = ArgumentParser()
    # parser.add_argument('-c', '--playercount', default = 1, help = 'Number of players to be deployed.')
    # parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Use verbose debugging mode.')
    # args = vars(parser.parse_args())
    # simulate(int(args["playercount"]), args["verbose"]))

    p = Player(verbose=True)
    p.connect()
    p.play()
    # p.shutdown()
