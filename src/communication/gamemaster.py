from src.communication.client import Client, ClientTypeTag
from src.communication.gameinfo import GameInfo
from src.communication import messages
import os
import xml.etree.ElementTree as ET


def get_game_attributes(file_name):
    full_file = os.getcwd() + file_name
    print(full_file)
    tree = ET.parse(full_file)
    root = tree.getroot()

    return root  # ET.tostring(root, encoding='unicode', method='xml')


def set_basic_shit():
    root = get_game_attributes("\GameMasterSettings.xml")

    game_name = ''
    number_of_players = 0

    for game_attributes in root.findall("{https://se2.mini.pw.edu.pl/17-pl-19/17-pl-19/}GameDefinition"):
        game_name = game_attributes.find("{https://se2.mini.pw.edu.pl/17-pl-19/17-pl-19/}GameName").text
        number_of_players = int(game_attributes.find('{https://se2.mini.pw.edu.pl/17-pl-19/17-pl-19/}NumberOfPlayersPerTeam').text)

    print("Game name: " + game_name + " Num of players: " + str(number_of_players))
    return game_name, number_of_players


class GameMaster(Client):
    def __init__(self, index=1, verbose=False):
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.GAMEMASTER
        self.info = GameInfo()
        self.gamename, self.numberofplayers = set_basic_shit()

    def run(self):
        self.send(messages.Message.registergame(messages.Message(), gamename=self.gamename, blueplayers=self.numberofplayers, redplayers=self.numberofplayers))

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
