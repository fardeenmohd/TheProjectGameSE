#!/usr/bin/env python
import os
import xml.etree.ElementTree as ET
from random import randint


def randomMessage():
    files = [f for f in os.listdir("../messages") if f.endswith(".xml")]
    index = randint(0, len(files) - 1)
    file_name = "../messages/" + files[index]
    full_file = os.path.abspath(os.path.join('../messages', file_name))
    tree = ET.parse(full_file)
    root = tree.getroot()

    messagetemp = ET.tostring(root, encoding = 'unicode', method = 'xml')
    message = str(messagetemp)
    return message


def getgames():
    """
    Figure 3.2: An example of GetGames message
    """

    file_name = 'getgames.xml'
    full_file = os.path.abspath(os.path.join('../messages', file_name))
    tree = ET.parse(full_file)
    root = tree.getroot()

    messagetemp = ET.tostring(root, encoding='utf8', method='xml')
    message = str(messagetemp)
    return message


class Message:
    message = ''

    def __init__(self):
        self.data = []

    # GetGames

    # RegisterGame
    def registergame(self, gamename, blueplayers, redplayers):
        """
        Figure 3.3: An example of RegisterGame message with a custom name and a two players teams setup.
        """

        file_name = 'registergame.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for newgameinfo in root.iter('{http://theprojectgame.mini.pw.edu.pl/}NewGameInfo'):
            newgameinfo.set('name', gamename)
            newgameinfo.set('blueTeamPlayers', str(blueplayers))
            newgameinfo.set('redTeamPlayers', str(redplayers))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # ConfirmGameRegistration
    def confirmgameregistration(self, gameid):
        """
        Figure 3.4: An example of ConfirmGameRegistration message assigning id 1 to the game.
        """

        file_name = 'confirmgameregistration.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for newgameinfo in root.iter('{http://theprojectgame.mini.pw.edu.pl/}ConfirmGameRegistration'):
            newgameinfo.set('gameId', str(gameid))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # RegisteredGames
    def registeredgames(self, gamename, blueplayers, redplayers):
        """
        Figure 3.5: An example of RegisteredGames message with two games listed.
        """

        numberofelements = len(gamename)  # number of games
        myattributes = []

        file_name = 'registeredgames.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for i in range(0, numberofelements):
            myattributes = {
                'name': str(gamename[i]),
                'blueTeamPlayers': str(blueplayers[i]),
                'redTeamPlayers': str(redplayers[i])
            }
            registeredgames = ET.SubElement(root, 'GameInfo', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # JoinGame
    def joingame(self, gamename, preferedRole, preferedTeam):
        """
        Figure 3.6: A JoinGame message with player trying to join, as the leader of a blue team,
        the game denoted as easyGame.
        """

        file_name = 'joingame.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for registeredgames in root.iter('{http://theprojectgame.mini.pw.edu.pl/}JoinGame'):
            registeredgames.set('gameName', gamename)
            registeredgames.set('preferedRole', str(preferedRole))
            registeredgames.set('preferedTeam', str(preferedTeam))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # ConfirmJoiningGame
    def confirmjoininggame(self, gameid, playerid, privateguid, id, team, type):
        """
        Figure 3.7: A ConfirmJoiningGame message setting the players unique Id and private GUID and informing
        about the Player’s role in the game.
        """

        file_name = 'confirmjoininggame.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for registeredgames in root.iter('{http://theprojectgame.mini.pw.edu.pl/}ConfirmJoiningGame'):
            registeredgames.set('gameId', str(gameid))
            registeredgames.set('playerId', str(playerid))
            registeredgames.set('privateGuid', str(privateguid))

        for registeredgames in root.iter('{http://theprojectgame.mini.pw.edu.pl/}PlayerDefinition'):
            registeredgames.set('id', str(id))
            registeredgames.set('team', str(team))
            registeredgames.set('type', str(type))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # GameMessage
    def gamemessage(self, playerid, playerteam, playertype, playersid, boardwidth, tasksheight, goalsheight, x, y):
        """
        Figure 3.8: A GameMessage for Player 2.
        """

        numberofplayers = len(playersid)

        file_name = 'gamemessage.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Game'):
            gamemassage.set('playerId', str(playerid))

        parent = ET.SubElement(root, 'Players')
        for i in range(0, numberofplayers):
            myattributes = {
                'team': str(playerteam[i]),
                'type': str(playertype[i]),
                'id': str(playersid[i])
            }
            ET.SubElement(parent, 'Player', attrib=myattributes)

        myattributes = {
            'width': str(boardwidth),
            'tasksHeight': str(tasksheight),
            'goalsHeight': str(goalsheight)
        }
        ET.SubElement(root, 'Board', attrib=myattributes)

        myattributes = {
            'x': str(x),
            'y': str(y)
        }
        ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # Discover
    def discover(self):
        """
        Figure 3.10: A Discover message from Player.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Discover xmlns="http://theprojectgame.mini.pw.edu.pl/"
                gameId="1"
                playerGuid="c094cab7-da7b-457f-89e5-a5c51756035f"
            />
        """
        return message

    # DataResponseForDiscover
    def dataresponsefordiscover(self):
        """
        Figure 3.11: A Data message response for the discover action.
        """

        message = """
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                    playerId="1"
                    gameFinished="false" >
                <TaskFields>
                    <TaskField x="1" y="4" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="1" />
                    <TaskField x="1" y="5" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="0" playerId="2" pieceId="2" />
                    <TaskField x="1" y="6" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="1" />
                    <TaskField x="0" y="4" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="2" />
                    <TaskField x="0" y="5" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="1" />
                    <TaskField x="0" y="6" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="2" />
                    <TaskField x="2" y="4" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="2" />
                    <TaskField x="2" y="5" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="1" />
                    <TaskField x="2" y="6" timestamp="2017-02-23T17:20:11"
                     distanceToPiece="2" />
                </TaskFields>
            </Data>
        """
        return message

    # MoveFromPlayer
    def movefromplayer(self):
        """
        Figure 3.12: A Move message from Player.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Move xmlns="http://theprojectgame.mini.pw.edu.pl/"
                 gameId="1"
                 playerGuid="c094cab7-da7b-457f-89e5-a5c51756035f"
                 direction="up"/>
        """
        return message

    # DataResponseForMove
    def dataresponseformove(self):
        """
        Figure 3.13: A Data message response for the proper move action.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                 playerId="1"
                 gameFinished="false">
                <TaskFields>
                    <TaskField x="1" y="5" timestamp="2017-02-23T17:20:11"
                             distanceToPiece="5" />
                </TaskFields>
                <PlayerLocation x="1" y="5" />
            </Data>
        """
        return message

    # DataResponseForMoveWhenFieldIsOccupied
    def dataresponseformovewhenfielisdoccupied(self):
        """
        Figure 3.14: A Data message response for the move action, when trying to enter an occupied field.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                 playerId="1"
                 gameFinished="false">
                  <TaskFields>
                        <TaskField x="1" y="5" timestamp="2017-02-23T17:20:11"
                                 distanceToPiece="0" playerId="2" pieceId="2" />
                  </TaskFields>
                  <Pieces>
                        <Piece id="2" timestamp="2017-02-23T17:20:11" playerId="2"
                              type="unknown" />
                  </Pieces>
                  <PlayerLocation x="1" y="4" />
            </Data>
        """
        return message

    # DataResponseForMoveOutOfBoard
    def dataresponseformoveoutofboard(self):
        """
        Figure 3.15: A Data message response for the move action, while trying to step out of the board.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                     playerId="1"
                     gameFinished="false">
                  <TaskFields>
                  </TaskFields>
                  <PlayerLocation x="1" y="7" />
            </Data>
        """
        return message

    # PickUpFromPlayer
    def pickupfromplayer(self):
        """
        Figure 3.16: A PickUp message from a Player.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <PickUpPiece
                xmlns="http://theprojectgame.mini.pw.edu.pl/"
                gameId="1"
                playerGuid="c094cab7-da7b-457f-89e5-a5c51756035f" />
        """
        return message

    # DataResponseForPickUp
    def dataresponseforpickup(self):
        """
        Figure 3.17: A Data message response for the piece pick up action.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                     playerId="1"
                     gameFinished="false">
                  <Pieces>
                        <Piece id="2" timestamp="2017-02-27T12:00:34" playerId="1" type="unknown" />
                  </Pieces>
            </Data>
        """
        return message

    # TestPiece
    def testpiece(self):
        """
        Figure 3.18: A TestPiece message from a Player.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <TestPiece xmlns="http://theprojectgame.mini.pw.edu.pl/"
                 gameId="1"
                 playerGuid="c094cab7-da7b-457f-89e5-a5c51756035f" />
        """
        return message

    # DataResponseForPlacingPiece
    def dataresponseforplacingpiece(self):
        """
        Figure 3.19: A Data message response for the placing of a piece action.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                     playerId="1"
                     gameFinished="false">
                  <Pieces>
                      <Piece id="2" type="sham" playerId="1" timestamp="2017-02-28T13:45:56" />
                  </Pieces>
            </Data>
        """
        return message

    # AuthorizeKnowledgeExchange
    def authorizeknowledgeexchange(self):
        """
        Figure 3.21: An AuthorizeKnowledgeExchange message.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <AuthorizeKnowledgeExchange xmlns="http://theprojectgame.mini.pw.edu.pl/"
                  withPlayerId="2"
                  gameId="1"
                  playerGuid="c094cab7-da7b-457f-89e5-a5c51756035f"
            />
        """
        return message

    # KnowledgeExchangeRequest
    def knowledgeexchangerequest(self):
        """
        Figure 3.22: A KnowledgeExchangeRequest message.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <KnowledgeExchangeRequest xmlns="http://theprojectgame.mini.pw.edu.pl/"
                  playerId="2"
                  senderPlayerId="1" />
        """
        return message

    # RejectKnowledgeExchange
    def rejectknowledgeexchange(self):
        """
        Figure 3.23: A RejectKnowledgeExchange message.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <RejectKnowledgeExchange xmlns="http://theprojectgame.mini.pw.edu.pl/"
                  permanent="false"
                  playerId="1"
                  senderPlayerId="2" />
        """
        return message

    # AcceptExchangeRequest
    def acceptexchangerequest(self):
        """
        Figure 3.24: An AcceptExchangeRequest message.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <AcceptExchangeRequest xmlns="http://theprojectgame.mini.pw.edu.pl/"
                  playerId="2"
                  senderPlayerId="2"
            />
        """
        return message

    # DataExchangeResponse
    def dataexchangeresponse(self):
        """
        Figure 3.25: A Data message with a knowledge exchange/accept exchange response data.
        """

        message = """
            <?xml version="1.0" encoding="utf-8"?>
            <Data xmlns="http://theprojectgame.mini.pw.edu.pl/"
                     playerId="1"
                     gameFinished="false">
                  <TaskFields>
                        <TaskField x="1" y="5" timestamp="2017-02-23T17:20:11" distanceToPiece="5" />
                        <TaskField x="1" y="4" timestamp="2017-02-23T17:20:13" distanceToPiece="4" />
                  </TaskFields>
                  <GoalFields>
                        <GoalField x="0" y="9" timestamp="2017-02-23T17:20:17" team="blue" type="non-goal"/>
                        <GoalField x="1" y="9" timestamp="2017-02-23T17:20:19" team="blue" type="goal" playerId="2"/>
                  </GoalFields>
                  <Pieces>
                        <Piece id="1" timestamp="2017-02-23T17:20:09" type="sham" />
                        <Piece id="2" timestamp="2017-02-23T17:19:09" type="unknown" />
                  </Pieces>
            </Data>
        """
        return message
