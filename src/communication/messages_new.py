#!/usr/bin/env python
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

def Move(game_id, player_guid, direction):
    root = __game_message("Move", game_id, player_guid)
    root.set("direction", direction)
    return __validate_encode(root)


def PickUp(game_id, player_guid):
    root = __game_message("PickUp", game_id, player_guid)
    return __validate_encode(root)


def GetGames():
    root = __base_message("GetGames")
    return __validate_encode(root)


def Place(game_id, player_guid):
    root = __game_message("Place", game_id, player_guid)
    return __validate_encode(root)

