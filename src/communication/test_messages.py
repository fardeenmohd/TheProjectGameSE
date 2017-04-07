from unittest import TestCase

from lxml.etree import DocumentInvalid

from src.communication.messages_new import *


class TestClass(TestCase):
    def test_move_invalid_guid(self):
        # try to generate a message with an invalid guid (not uuid4)
        game_id = 12
        player_guid = 12
        direction = 'up'

        flag = False  # will be set to True if there is an error with the message.
        try:
            Move(game_id, player_guid, direction)
        except DocumentInvalid:
            flag = True

        assert flag

    def test_getgames(self):
        # check if generated GetGames xml is the same as the example

        generated_xml = GetGames()
        sample_xml = open("../messages/GetGames.xml").read()

        assert generated_xml == sample_xml

    def test_placepiece(self):
        # check if generated PlacePlace xml is the same as the example
        game_id = 1
        player_guid = 'c094cab7-da7b-457f-89e5-a5c51756035f'

        generated_xml = PlacePiece(game_id, player_guid)
        sample_xml = open("../messages/PlacePiece.xml").read()  # Discover, TestPiece, PlacePiece, PickUpPiece

        assert generated_xml == sample_xml

    def test_authorizeknowledgeexchange(self):
        # check if generated PlacePlace xml is the same as the example
        game_id = 1
        player_guid = 'c094cab7-da7b-457f-89e5-a5c51756035f'
        with_player_id = 3

        generated_xml = AuthorizeKnowledgeExchange(game_id, player_guid, with_player_id)
        sample_xml = open("../messages/AuthorizeKnowledgeExchange.xml").read()  # Discover, TestPiece, PlacePiece, PickUpPiece

        assert generated_xml == sample_xml
