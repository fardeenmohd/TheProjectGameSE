#!/usr/bin/env python
from datetime import datetime

from lxml import etree

# constants:
XSD_PATH = "../messages/TheProjectGameCommunication.xsd"
XML_NAMESPACE = "https://se2.mini.pw.edu.pl/17-results/"
NAMESPACE_PREFIX = "{%s}" % XML_NAMESPACE
NSMAP = {None: XML_NAMESPACE}

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
    return etree.Element(NAMESPACE_PREFIX + message_name, nsmap=NSMAP)


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


def __append_element(root, tag, attrib=None):
    return etree.SubElement(root, NAMESPACE_PREFIX + tag, attrib, NSMAP)


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
        __append_element(root, etree.Element("PlayerLocation", e_player_location))

    # add TaskFields collection:
    if task_fields is not None:
        c_task_fields = __append_element(root, "TaskFields")

        # add each TaskField to the collection:
        for (x, y), field in task_fields:
            e_attributes = {"x": str(x), "y": str(y), "timestamp": datetime.now(),
                            "distanceToPiece": str(field.distance_to_piece)}
            if field.player_id is not None:
                e_attributes["playerId"] = str(field.player_id)
            if field.piece_id is not None:
                e_attributes["pieceID"] = str(field.piece_id)
            __append_element(c_task_fields, "TaskField", e_attributes)

    # add GoalFields collection:
    if goal_fields is not None:
        c_goal_fields = __append_element(root, "GoalFields")

        # add each GoalField to the collection:
        for (x, y), field in goal_fields.items():
            e_attributes = {"x": str(x), "y": str(y), "timestamp": datetime.now(), "type": field.type,
                            "team": field.allegiance}
            if field.player_id is not None:
                e_attributes["playerId"] = str(field.player_id)
            if field.piece_id is not None:
                e_attributes["pieceID"] = str(field.piece_id)
            __append_element(c_goal_fields, "GoalField", e_attributes)

    # add Pieces collection:
    if pieces is not None:
        c_pieces = __append_element(root, "Pieces")

        # add each Piece to the collection:
        for piece in pieces.values():
            e_attributes = {"id": piece.id, "timestamp": datetime.now(), "type": piece.type}
            if piece.player_id is not None:
                e_attributes["playerId"] = piece.player_id
            __append_element(c_pieces, "Piece", e_attributes)

    return __validate_encode(root)


def game(player_id, teams: dict, board_width, tasks_height, goals_height, player_location: tuple):
    """
    :param teams: A dict of dicts: team => {player_id => type}
    :param player_location: a tuple (x,y)
    """
    root = __player_message("Game", player_id)

    # add PlayerLocation element:
    if player_location is not None:
        e_player_location = {"x": str(player_location[0]), "y": str(player_location[1])}
        __append_element(root, "PlayerLocation", e_player_location)

    # add Players collection
    c_players = __append_element(root, "Players")

    # add each Player to the collection:
    for team in teams.values():
        for player_id, type in team.items():
            e_attributes = {"id": player_id, "type": type, "team": team}
            __append_element(c_players, "Player", e_attributes)

    # add Board element:
    e_board_attributes = {"width": str(board_width), "tasksHeight": str(tasks_height), "goalsHeight": str(goals_height)}
    __append_element(root, "Board", e_board_attributes)

    return __validate_encode(root)


def knowledge_exchange_request(player_id, sender_player_id):
    root = __between_players_message("KnowledgeExchangeRequest", player_id, sender_player_id)
    return __validate_encode(root)


def accept_exchange_request(player_id, sender_player_id):
    root = __between_players_message("AcceptExchangeRequest", player_id, sender_player_id)
    return __validate_encode(root)


def reject_knowledge_exchange(player_id, sender_player_id, permanent):
    root = __between_players_message("RejectKnowledgeExchange", player_id, sender_player_id)
    root.set("permanent", str(permanent).lower())
    return __validate_encode(root)


def register_game(game_name, blue_team_players, red_team_players):
    root = __base_message("RegisterGame")
    __append_element(root, "NewGameInfo", {"gameName": game_name, "redTeamPlayers": str(red_team_players),
                                           "blueTeamPlayers": str(blue_team_players)})
    return __validate_encode(root)


def confirm_game_registration(game_id):
    root = __base_message("ConfirmGameRegistration")
    root.set("gameId", str(game_id))
    return __validate_encode(root)


def reject_game_registration(game_name):
    root = __base_message("RejectGameRegistration")
    root.set("gameName", str(game_name))
    return __validate_encode(root)


def game_started(game_id):
    root = __base_message("GameStarted")
    root.set("gameId", str(game_id))
    return __validate_encode(root)


def registered_games(games: dict):
    """
    :param games: a dict of: game_id => GameInfo
    """
    root = __base_message("RegisteredGames")
    for game in games.values():
        if game.open is True:
            e_attributes = {"gameName": game.name, "redTeamPlayers": str(game.max_red_players),
                            "blueTeamPlayers": str(game.max_blue_players)}
            __append_element(root, "GameInfo", e_attributes)
    return __validate_encode(root)


def join_game(game_name, pref_team, pref_type, player_id=None):
    root = __base_message("JoinGame")
    root.set("gameName", game_name)
    root.set("preferredTeam", pref_team)
    root.set("preferredRole", pref_type)
    if player_id is not None:
        root.set("playerId", player_id)
    return __validate_encode(root)


def confirm_joining_game(player_id, game_id, player_guid, team, type):
    root = __player_message("ConfirmJoiningGame", player_id)
    root.set("privateGuid", str(player_guid))
    root.set("gameId", game_id)
    e_definition_attributes = {"id": player_id, "type": type, "team": team}
    __append_element(root, "PlayerDefinition", e_definition_attributes)
    return __validate_encode(root)


def reject_joining_game(player_id, game_name):
    root = __player_message("RejectJoiningGame", player_id)
    root.set("gameName", game_name)
    return __validate_encode(root)


def game_master_disconnected(game_id):
    root = __base_message("GameMasterDisconnected")
    root.set("gameId", game_id)
    return __validate_encode(root)


def player_disconnected(player_id):
    root = __player_message("PlayerDisconnected", player_id)
    return __validate_encode(root)
