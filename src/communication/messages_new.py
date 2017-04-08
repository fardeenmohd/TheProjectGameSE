#!/usr/bin/env python
from datetime import datetime

from lxml import etree

# constants:
XSD_PATH = "../messages/TheProjectGameCommunication.xsd"
XML_NAMESPACE = "https://se2.mini.pw.edu.pl/17-results/"

# pre-load the XML schema:
SCHEMA = etree.XMLSchema(etree.parse(XSD_PATH))


def __validate_encode(root):
    """
    check if an XML message root is valid against the SCHEMA, return it in string form
    :return: root encoded as unicode string.
    """
    SCHEMA.assertValid(root)
    return etree.tostring(root, encoding='unicode')


def __base_message(message_name) -> etree.ElementBase:
    """
    :returns an xml root for the communication in this Project (with set namespaces)
    """
    namespace_prefix = "{%s}" % XML_NAMESPACE
    return etree.Element(namespace_prefix + message_name, nsmap={None: XML_NAMESPACE})


def __game_message(message_name, game_id, player_guid) -> etree.ElementBase:
    """
    :returns an xml root with GameMessage as its base (look at the schema for reference)
    used in messages sent from Player to GM (e.g. Move, PickUp...)
    """
    root = __base_message(message_name)
    root.set("gameId", str(game_id))
    root.set("playerGuid", str(player_guid))
    return root


def __player_message(message_name, player_id) -> etree.ElementBase:
    """
    :returns an xml root with PlayerMessage as its base (again, look at the schema for reference)
    used in messages sent to Player from GM or Server (e.g. Data, Game, ConfirmJoiningGame...)
    """
    root = __base_message(message_name)
    root.set("playerId", str(player_id))
    return root


def __between_players_message(message_name, player_id, sender_player_id) -> etree.ElementBase:
    """
    :returns an xml root with BetweenPlayerMessage as its base (again, look at the schema for reference)
    used in messages sent from Player to Player (e.g. KnowledgeExchangeRequest...)
    """
    root = __player_message(message_name, player_id)
    root.set("senderPlayerId", sender_player_id)
    return root


# TODO: change message-method names (e.g. move, pickup) in this file to CamelCase (use PyCharm's Refactor->Rename tool)
# (so, after refactoring the names should be e.g. Move, PickUp, JoinGame...)

def move(game_id, player_guid, direction):
    root = __game_message("Move", game_id, player_guid)
    root.set("direction", direction)
    return __validate_encode(root)


def pick_up_piece(game_id, player_guid):
    root = __game_message("PickUpPiece", game_id, player_guid)
    return __validate_encode(root)


def place_piece(game_id, player_guid):
    root = __game_message("PlacePiece", game_id, player_guid)
    return __validate_encode(root)


def test_piece(game_id, player_guid):
    root = __game_message("TestPiece", game_id, player_guid)
    return __validate_encode(root)


def discover(game_id, player_guid):
    root = __game_message("Discover", game_id, player_guid)
    return __validate_encode(root)


def authorize_knowledge_exchange(game_id, player_guid, with_player_id):
    root = __game_message("AuthorizeKnowledgeExchange", game_id, player_guid)
    root.set("withPlayerId", str(with_player_id))
    return __validate_encode(root)


def get_games():
    root = __base_message("GetGames")
    return __validate_encode(root)


def data(player_id, game_finished: bool, task_fields: dict = None, goal_fields: dict = None, pieces: dict = None,
         player_location=None):
    """
    :param player_location: tuple (x,y)
    """
    root = __player_message("Data", player_id)
    root.set("gameFinished", str(game_finished).lower())

    # add PlayerLocation element:
    if player_location is not None:
        e_player_location = {"x": str(player_location[0]), "y": str(player_location[1])}
        root.append(etree.Element("PlayerLocation", e_player_location))

    # add TaskFields collection:
    if task_fields is not None:
        c_task_fields = etree.Element("TaskFields")

        # add each TaskField to the collection:
        for (x, y), field in task_fields:
            e_attributes = {"x": str(x), "y": str(y), "timestamp": datetime.now(),
                            "distanceToPiece": str(field.distance_to_piece)}
            if field.player_id is not None:
                e_attributes["playerId"] = str(field.player_id)
            if field.piece_id is not None:
                e_attributes["pieceID"] = str(field.piece_id)
            e_field = etree.Element("TaskField", e_attributes)
            c_task_fields.append(e_field)

        root.append(c_task_fields)

    # add GoalFields collection:
    if goal_fields is not None:
        c_goal_fields = etree.Element("GoalFields")

        # add each GoalField to the collection:
        for (x, y), field in goal_fields.items():
            e_attributes = {"x": str(x), "y": str(y), "timestamp": datetime.now(), "type": field.type,
                            "team": field.allegiance}
            if field.player_id is not None:
                e_attributes["playerId"] = str(field.player_id)
            if field.piece_id is not None:
                e_attributes["pieceID"] = str(field.piece_id)
            e_field = etree.Element("GoalField", e_attributes)
            c_goal_fields.append(e_field)

        root.append(c_goal_fields)

    # add Pieces collection:
    if pieces is not None:
        c_pieces = etree.Element("Pieces")

        # add each Piece to the collection:
        for piece in pieces.values():
            e_attributes = {"id": piece.id, "timestamp": datetime.now(), "type": piece.type}
            if piece.player_id is not None:
                e_attributes["playerId"] = piece.player_id
            e_piece = etree.Element("Piece", e_attributes)
            c_pieces.append(e_piece)

        root.append(c_pieces)
    return __validate_encode(root)


def game(player_id, teams: dict, board_width, tasks_height, goals_height, player_location: tuple):
    """
    :param teams: A dict of dicts: team => {player_id => role}
    :param player_location: a tuple (x,y)
    """
    root = __player_message("Game", player_id)

    # add PlayerLocation element:
    if player_location is not None:
        e_player_location = {"x": str(player_location[0]), "y": str(player_location[1])}
        root.append(etree.Element("PlayerLocation", e_player_location))

    # add Players collection
    c_players = etree.Element("Players")

    # add each Player to the collection:
    for team in teams.values():
        for player_id, role in team.items():
            e_attributes = {"id": player_id, "role": role, "team": team}
            e_player = etree.Element("Player", e_attributes)
            c_players.append(e_player)
    root.append(c_players)

    # add Board element:
    board_attributes = {"width": str(board_width), "tasksHeight": str(tasks_height), "goalsHeight": str(goals_height)}
    e_board = etree.Element("Board", board_attributes)
    root.append(e_board)

    return __validate_encode(root)
