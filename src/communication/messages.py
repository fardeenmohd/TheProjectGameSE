#!/usr/bin/env python
# coding=utf-8
import os
import xml.etree.ElementTree as ET
from time import gmtime, strftime

# WARNING: THIS FILE SUFFERS FROM MALARIA
# TOUCH AT OWN RISK

ROOT_DICTIONARY = {}
ET.register_namespace('', "https://se2.mini.pw.edu.pl/17-results/")
data = []

files = [f for f in os.listdir("../messages") if f.endswith(".xml")]
for file in files:
    file_name = "../messages/" + file

    message_name = file.split('.')[0]

    full_file = os.path.abspath(os.path.join('../messages', file_name))
    tree = ET.parse(full_file)
    root = tree.getroot()

    ROOT_DICTIONARY[message_name] = root


# **** MESSAGES ****

# AcceptExchangeRequest
def accept_exchange_request(playerid, senderplayerid):
    """
    Figure 3.24: An AcceptExchangeRequest message.
    """

    root = ROOT_DICTIONARY['AcceptexchangeRequest']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}AcceptExchangeRequest'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('senderPlayerId', str(senderplayerid))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# AuthorizeKnowledgeExchange
def authorize_knowledge_exchange(withplayerid, gameid, playerguid):
    """
    Figure 3.21: An AuthorizeKnowledgeExchange message.
    """

    root = ROOT_DICTIONARY['AuthorizeKnowledgeExchange']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}AuthorizeKnowledgeExchange'):
        gamemassage.set('withPlayerId', str(withplayerid))
        gamemassage.set('gameId', str(gameid))
        gamemassage.set('playerGuid', str(playerguid))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# ConfirmGameRegistration
def confirm_game_registration(gameid):
    """
    Figure 3.4: An example of ConfirmGameRegistration message assigning id 1 to the game.
    """

    root = ROOT_DICTIONARY['ConfirmGameRegistration']

    for new_game in root.iter('{http://theprojectgame.mini.pw.edu.pl/}ConfirmGameRegistration'):
        new_game.set('gameId', str(gameid))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# ConfirmJoiningGame
def confirm_joining_game(gameid, privateguid, id, team, type):
    """
    Figure 3.7: A ConfirmJoiningGame message setting the players unique Id and private GUID and informing
    about the Client’s role in the game.
    """

    root = ROOT_DICTIONARY['ConfirmJoinInGgame']

    for registeredgames in root.iter('{http://theprojectgame.mini.pw.edu.pl/}ConfirmJoiningGame'):
        registeredgames.set('gameId', str(gameid))
        registeredgames.set('playerId', str(id))
        registeredgames.set('privateGuid', str(privateguid))

    for registeredgames in root.iter('{http://theprojectgame.mini.pw.edu.pl/}PlayerDefinition'):
        registeredgames.set('id', str(id))
        registeredgames.set('team', str(team))
        registeredgames.set('type', str(type))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# Discover
def discover(gameid, playerguide):
    """
    Figure 3.10: A Discover message from Client.
    """

    root = ROOT_DICTIONARY['Discover']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Discover'):
        gamemassage.set('gameId', str(gameid))
        gamemassage.set('playerGuid', str(playerguide))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# DiscoverResponse (old - dataresponsefordiscover)
def discover_response(playerid, gamefinished, taskfieldsX, taskfieldsY, taskfieldsdistances, pieceid, piecetype):
    """
    Figure 3.11: A Data message response for the discover action.
    """
    numberoftaskfields = len(taskfieldsX)

    root = ROOT_DICTIONARY['DiscoverResponse']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'TaskFields')
    for i in range(0, numberoftaskfields):
        myattributes = {'x': str(taskfieldsX[i]), 'y': str(taskfieldsY[i]),
                        'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                        'distanceToPiece': str(taskfieldsdistances[i])}
        ET.SubElement(parent, 'TaskField', attrib=myattributes)

    parent = ET.SubElement(root, 'Pieces')
    myattributes = {'id': str(pieceid), 'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                    'type': str(piecetype)}
    ET.SubElement(parent, 'Piece', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# Game (OLD - gamemessage)
def game(playerid, playerteam, playertype, playersid, boardwidth, tasksheight, goalsheight, x, y):
    """
    Figure 3.8: A GameMessage for Client 2.
    """

    numberofplayers = len(playersid)

    root = ROOT_DICTIONARY['GameMessage']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Game'):
        gamemassage.set('playerId', str(playerid))

    parent = ET.SubElement(root, 'Players')
    for i in range(0, numberofplayers):
        myattributes = {'team': str(playerteam[i]), 'type': str(playertype[i]), 'id': str(playersid[i])}
        ET.SubElement(parent, 'Client', attrib=myattributes)

    myattributes = {'width': str(boardwidth), 'tasksHeight': str(tasksheight), 'goalsHeight': str(goalsheight)}
    ET.SubElement(root, 'Board', attrib=myattributes)

    myattributes = {'x': str(x), 'y': str(y)}
    ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# GetGames
def get_games():
    """
    Figure 3.2: An example of GetGames message
    """

    root = ROOT_DICTIONARY['GetGames']

    message_temp = ET.tostring(root, encoding='unicode')
    message = str(message_temp)
    return message


# JoinGame
def join_game(gamename, preferedRole, preferedTeam):
    """
    Figure 3.6: A JoinGame message with player trying to join, as the leader of a blue team,
    the game denoted as easyGame.
    """

    root = ROOT_DICTIONARY['JoinGame']

    root.attrib["gameName"] = gamename
    root.attrib["preferedRole"] = preferedRole
    root.attrib["preferedTeam"] = preferedTeam

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# KnowledgeExchangeReject
def knowledge_exchange_reject(permanent, playerid, senderplayerid):
    """
    Figure 3.23: A RejectKnowledgeExchange message.
    """

    root = ROOT_DICTIONARY['RejectKnowledgeExchange']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}RejectKnowledgeExchange'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('senderPlayerId', str(senderplayerid))
        gamemassage.set('permanent', str(permanent))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# KnowledgeExchangeRequest
def knowledge_exchange_request(playerid, senderplayerid):
    """
    Figure 3.22: A KnowledgeExchangeRequest message.
    """

    root = ROOT_DICTIONARY['KnowledgeExchangeRequest']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}KnowledgeExchangeRequest'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('senderPlayerId', str(senderplayerid))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# KnowledgeExchangeResponse
def knowledge_exchange_response(playerid, gamefinished, xtaskfield, ytaskfield, distancetopiece, xgoalfield, ygoalfield,
                                team, fieldtype, goalfieldplayerid,
                                pieceid, piecetype):
    """
    Figure 3.25: A Data message with a knowledge exchange/accept exchange response data.
    """

    numberoffields = len(xtaskfield)
    numberofgoals = len(xgoalfield)
    numberofpieces = len(pieceid)

    root = ROOT_DICTIONARY['KnowledgeExchangeResponse']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'TaskFields')
    for i in range(0, numberoffields):
        my_attributes = {'x': str(xtaskfield[i]), 'y': str(ytaskfield[i]),
                         'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                         'distanceToPiece': str(distancetopiece[i])}
        ET.SubElement(parent, 'TaskField', attrib=my_attributes)

    parent = ET.SubElement(root, 'GoalFields')
    for i in range(0, numberofgoals):
        my_attributes = {'x': str(xgoalfield[i]), 'y': str(ygoalfield[i]),
                         'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())), 'team': str(team[i]),
                         'type': str(fieldtype[i]), 'playerId': str(goalfieldplayerid[i])}
        ET.SubElement(parent, 'GoalField', attrib=my_attributes)

    parent = ET.SubElement(root, 'Pieces')
    for i in range(0, numberofpieces):
        my_attributes = {'id': str(pieceid[i]), 'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                         'piecetype': str(piecetype[i])}
        ET.SubElement(parent, 'Piece', attrib=my_attributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# Move
def move(gameid, playerguide, direction):
    """
    Figure 3.12: A Move message from Client.
    """

    root = ROOT_DICTIONARY['Move']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Move'):
        gamemassage.set('gameId', str(gameid))
        gamemassage.set('playerGuid', str(playerguide))
        gamemassage.set('direction', str(direction))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# MoveResponseEdge
def move_response_edge(playerid, gamefinished, playerlocationx, playerlocationy):
    """
    Figure 3.15: A Data message response for the move action, while trying to step out of the board.
    """

    numberoftaskfields = 1

    root = ROOT_DICTIONARY['MoveResponsePlayer']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'TaskFields')
    for i in range(0, numberoftaskfields):
        ET.SubElement(parent, 'TaskField')

    myattributes = {'x': str(playerlocationx), 'y': str(playerlocationy)}
    ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# MoveResponseGood
def move_response_good(playerid, gamefinished, taskfieldsX, taskfieldsY, taskfieldsdistances, playerlocationx,
                       playerlocationy):
    """
    Figure 3.13: A Data message response for the proper move action.
    """

    numberoftaskfields = 1

    root = ROOT_DICTIONARY['MoveResponseGood']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'TaskFields')
    for i in range(0, numberoftaskfields):
        myattributes = {'x': str(taskfieldsX[i]), 'y': str(taskfieldsY[i]),
                        'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                        'distanceToPiece': str(taskfieldsdistances[i])}
        ET.SubElement(parent, 'TaskField', attrib=myattributes)

    myattributes = {'x': str(playerlocationx), 'y': str(playerlocationy)}
    ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# MoveResponsePlayer
def move_response_player(playerid, gamefinished, taskfieldsX, taskfieldsY, taskfieldsdistances, playerlocationx,
                         playerlocationy, pieceid, piecetype):
    """
    Figure 3.14: A Data message response for the move action, when trying to enter an occupied field.
    """

    numberoftaskfields = 1

    root = ROOT_DICTIONARY['MoveResponsePlayer']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'TaskFields')
    for i in range(0, numberoftaskfields):
        myattributes = {'x': str(taskfieldsX[i]), 'y': str(taskfieldsY[i]),
                        'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                        'distanceToPiece': str(taskfieldsdistances[i]), 'playerId': str(playerid),
                        'pieceId': str(pieceid)}
        ET.SubElement(parent, 'TaskField', attrib=myattributes)

    myattributes = {'x': str(playerlocationx), 'y': str(playerlocationy)}
    ET.SubElement(root, 'PlayerLocation', attrib=myattributes)

    parent = ET.SubElement(root, 'Pieces')
    myattributes = {'id': str(pieceid), 'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                    'playerId': str(playerid), 'type': str(piecetype)}
    ET.SubElement(parent, 'Piece', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# PickUp
def pickup(gameid, playerguide):
    """
    Figure 3.16: A PickUp Piece message from a Client.
    """

    root = ROOT_DICTIONARY['PickUp']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}PickUpPiece'):
        gamemassage.set('gameId', str(gameid))
        gamemassage.set('playerGuid', str(playerguide))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# PickUpResponse
def pickup_response(playerid, gamefinished, pieceid, piecetype):
    """
    Figure 3.17: A Data message response for the piece pick up action.
    """

    root = ROOT_DICTIONARY['PickUpResponse']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'Pieces')

    myattributes = {'id': str(pieceid), 'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())),
                    'playerId': str(playerid), 'type': str(piecetype)}
    ET.SubElement(parent, 'Piece', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# PlaceResponse
def place_response(playerid, gamefinished, pieceid, piecetype):
    """
    Figure 3.19: A Data message response for the placing of a piece action.
    """

    root = ROOT_DICTIONARY['PickUpResponse']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}Data'):
        gamemassage.set('playerId', str(playerid))
        gamemassage.set('gameFinished', str(gamefinished))

    parent = ET.SubElement(root, 'Pieces')

    myattributes = {'id': str(pieceid), 'type': str(piecetype),
                    'timestamp': str(strftime("%Y-%m-%dT%H:%M:%S", gmtime())), 'playerId': str(playerid)}
    ET.SubElement(parent, 'Piece', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# RegisteredGames
def registered_games(games):
    """
    Figure 3.5: An example of RegisteredGames message with two games listed.
    :type games: dict
    """

    root = ROOT_DICTIONARY['RegisteredGames']

    for game_index, game_info in games.items():
        myattributes = {'gameName': game_info.name, 'blueTeamPlayers': str(game_info.blue_players),
                        'redTeamPlayers': str(game_info.red_players)}
        registeredgames = ET.SubElement(root, 'GameInfo', attrib=myattributes)

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)

    return message


# RegisterGame
def register_game(gamename, blueplayers, redplayers):
    """
    Figure 3.3: An example of RegisterGame message with a custom name and a two players teams setup.
    """

    root = ROOT_DICTIONARY['RegisterGame']

    for newgameinfo in root.iter('{http://theprojectgame.mini.pw.edu.pl/}NewGameInfo'):
        newgameinfo.set('name', gamename)
        newgameinfo.set('blueTeamPlayers', str(blueplayers))
        newgameinfo.set('redTeamPlayers', str(redplayers))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


def reject_game_registration():
    root = ROOT_DICTIONARY["RejectGameRegistration"]
    return str(ET.tostring(root, encoding='unicode', method='xml'))


def reject_joining_game(game_name, player_id):
    root = ROOT_DICTIONARY['RejectJoiningGame']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}RejectJoiningGame'):
        gamemassage.set('gameName', str(game_name))
        gamemassage.set('plerId', str(player_id))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message


# TestPiece
def test_piece(gameid, playerguide):
    """
    Figure 3.18: A TestPiece message from a Client.
    """

    root = ROOT_DICTIONARY['TestPiece']

    for gamemassage in root.iter('{http://theprojectgame.mini.pw.edu.pl/}TestPiece'):
        gamemassage.set('gameId', str(gameid))
        gamemassage.set('playerGuid', str(playerguide))

    messagetemp = ET.tostring(root, encoding='unicode', method='xml')
    message = str(messagetemp)
    return message

##########################################
# brakuje:
# GameMasterDisconnected, GameStarted, Place, PlayerDisconnected, RejectGameRegistration, RejectJoiningGame
