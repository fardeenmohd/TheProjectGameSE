from src.communication.client import Client, ClientTypeTag
from src.communication.gameinfo import GameInfo


class GameMaster(Client):
	def __init__(self, index = 1, verbose = False):
		super().__init__(index, verbose)

		self.typeTag = ClientTypeTag.GAMEMASTER
		self.info = GameInfo()

	def run(self):
		# TODO: register a game and do other stuff
		1 + 1


if __name__ == '__main__':
	# parser = ArgumentParser()
	# parser.add_argument('-c', '--gamemastercount', default = 1, help = 'Number of gamemasters to be deployed.')
	# parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = 'Use verbose debugging mode.')
	# args = vars(parser.parse_args())
	# simulate(int(args["gamemastercount"]), args["verbose"]))
	gm = GameMaster(verbose = True)
	gm.connect()
	gm.run()
	gm.shutdown()
