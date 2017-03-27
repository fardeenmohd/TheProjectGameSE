#!/usr/bin/env python
import os
import xml.etree.ElementTree as ET
from random import randint
from time import gmtime, strftime


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

    file_name = 'GetGames.xml'
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

        file_name = 'RegisterGame.xml'
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

        file_name = 'ConfirmGameRegistration.xml'
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

        file_name = 'RegisteredGames.xml'
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

        file_name = 'JoinGame.xml'
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

        file_name = 'ConfirmJoinInGgame.xml'
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

        file_name = 'GameMessage.xml'
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
    def discover(self, gameid, playerguide):
        """
        Figure 3.10: A Discover message from Player.
        """

        file_name = 'Discover.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Discover'):
            gamemassage.set('gameId', str(gameid))
            gamemassage.set('playerGuid', str(playerguide))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # DataResponseForDiscover
    def dataresponsefordiscover(self, playerid, gamefinished, taskfieldsX, taskfieldsY, taskfieldsdistances, pieceid, piecetype):
        """
        Figure 3.11: A Data message response for the discover action.
        """
        numberoftaskfields = len(taskfieldsX)

        file_name = 'DiscoverResponse.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('gameFinished', str(gamefinished))

        parent = ET.SubElement(root, 'TaskFields')
        for i in range(0, numberoftaskfields):
            myattributes = {
                'x': str(taskfieldsX[i]),
                'y': str(taskfieldsY[i]),
                'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                'distanceToPiece': str(taskfieldsdistances[i])}
            ET.SubElement(parent, 'TaskField', attrib=myattributes)

        parent = ET.SubElement(root, 'Pieces')
        myattributes = {
            'id': str(pieceid),
            'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
            'type': str(piecetype)
        }
        ET.SubElement(parent, 'Piece', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # Move
    def move(self, gameid, playerguide, direction):
        """
        Figure 3.12: A Move message from Player.
        """

        file_name = 'Move.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Move'):
            gamemassage.set('gameId', str(gameid))
            gamemassage.set('playerGuid', str(playerguide))
            gamemassage.set('direction', str(direction))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # MoveResponseGood
    def moveresponsegood(self, playerid, gamefinished, taskfieldsX, taskfieldsY, taskfieldsdistances, playerlocationx, playerlocationy):
        """
        Figure 3.13: A Data message response for the proper move action.
        """

        numberoftaskfields = 1

        file_name = 'MoveResponseGood.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('gameFinished', str(gamefinished))

        parent = ET.SubElement(root, 'TaskFields')
        for i in range(0, numberoftaskfields):
            myattributes = {
                'x': str(taskfieldsX[i]),
                'y': str(taskfieldsY[i]),
                'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                'distanceToPiece': str(taskfieldsdistances[i])}
            ET.SubElement(parent, 'TaskField', attrib=myattributes)

        myattributes = {
            'x': str(playerlocationx),
            'y': str(playerlocationy)
        }
        ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # MoveResponsePlayer
    def moveresponseplayer(self, playerid, gamefinished, taskfieldsX, taskfieldsY, taskfieldsdistances, playerlocationx, playerlocationy, pieceid, piecetype):
        """
        Figure 3.14: A Data message response for the move action, when trying to enter an occupied field.
        """

        numberoftaskfields = 1

        file_name = 'MoveResponsePlayer.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('gameFinished', str(gamefinished))

        parent = ET.SubElement(root, 'TaskFields')
        for i in range(0, numberoftaskfields):
            myattributes = {
                'x': str(taskfieldsX[i]),
                'y': str(taskfieldsY[i]),
                'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                'distanceToPiece': str(taskfieldsdistances[i]),
                'playerId': str(playerid),
                'pieceId': str(pieceid)}
            ET.SubElement(parent, 'TaskField', attrib=myattributes)

        myattributes = {
            'x': str(playerlocationx),
            'y': str(playerlocationy)
        }
        ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

        parent = ET.SubElement(root, 'Pieces')
        myattributes = {
            'id': str(pieceid),
            'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
            'playerId': str(playerid),
            'type': str(piecetype)
        }
        ET.SubElement(parent, 'Piece', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # MoveResponseEdge
    def moveresponseedge(self, playerid, gamefinished, playerlocationx, playerlocationy):
        """
        Figure 3.15: A Data message response for the move action, while trying to step out of the board.
        """

        numberoftaskfields = 1

        file_name = 'MoveResponsePlayer.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('gameFinished', str(gamefinished))

        parent = ET.SubElement(root, 'TaskFields')
        for i in range(0, numberoftaskfields):
            ET.SubElement(parent, 'TaskField')

        myattributes = {
            'x': str(playerlocationx),
            'y': str(playerlocationy)
        }
        ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # PickUp
    def pickup(self, gameid, playerguide):
        """
        Figure 3.16: A PickUp Piece message from a Player.
        """

        file_name = 'PickUp.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}PickUpPiece'):
            gamemassage.set('gameId', str(gameid))
            gamemassage.set('playerGuid', str(playerguide))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # PickUpResponse
    def pickupresponse(self, playerid, gamefinished, pieceid, piecetype):
        """
        Figure 3.17: A Data message response for the piece pick up action.
        """

        file_name = 'PickUpResponse.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('gameFinished', str(gamefinished))

        parent = ET.SubElement(root, 'Pieces')

        myattributes = {
            'id': str(pieceid),
            'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
            'playerId': str(playerid),
            'type': str(piecetype)
        }
        ET.SubElement(parent, 'Piece', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # TestPiece
    def testpiece(self, gameid, playerguide):
        """
        Figure 3.18: A TestPiece message from a Player.
        """

        file_name = 'TestPiece.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}TestPiece'):
            gamemassage.set('gameId', str(gameid))
            gamemassage.set('playerGuid', str(playerguide))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # PlaceResponse
    def placeresponse(self, playerid, gamefinished, pieceid, piecetype):
        """
        Figure 3.19: A Data message response for the placing of a piece action.
        """

        file_name = 'PickUpResponse.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('gameFinished', str(gamefinished))

        parent = ET.SubElement(root, 'Pieces')

        myattributes = {
            'id': str(pieceid),
            'type': str(piecetype),
            'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
            'playerId': str(playerid)
        }
        ET.SubElement(parent, 'Piece', attrib=myattributes)

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # AuthorizeKnowledgeExchange
    def authorizeknowledgeexchange(self, withplayerid, gameid, playerguid):
        """
        Figure 3.21: An AuthorizeKnowledgeExchange message.
        """

        file_name = 'AuthorizeKnowledgeExchange.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}AuthorizeKnowledgeExchange'):
            gamemassage.set('withPlayerId', str(withplayerid))
            gamemassage.set('gameId', str(gameid))
            gamemassage.set('playerGuid', str(playerguid))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # KnowledgeExchangeRequest
    def knowledgeexchangerequest(self, playerid, senderplayerid):
        """
        Figure 3.22: A KnowledgeExchangeRequest message.
        """

        file_name = 'KnowledgeExchangeRequest.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}KnowledgeExchangeRequest'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('senderPlayerId', str(senderplayerid))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
        return message

    # RejectKnowledgeExchange
    def rejectknowledgeexchange(self, permanent, playerid, senderplayerid):
        """
        Figure 3.23: A RejectKnowledgeExchange message.
        """

        file_name = 'RejectKnowledgeExchange.xml'
        full_file = os.path.abspath(os.path.join('../messages', file_name))
        tree = ET.parse(full_file)
        root = tree.getroot()

        for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}RejectKnowledgeExchange'):
            gamemassage.set('playerId', str(playerid))
            gamemassage.set('senderPlayerId', str(senderplayerid))
            gamemassage.set('permanent', str(permanent))

        messagetemp = ET.tostring(root, encoding='utf8', method='xml')
        message = str(messagetemp)
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
