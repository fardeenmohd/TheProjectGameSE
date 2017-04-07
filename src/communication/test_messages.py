from unittest import TestCase

from lxml.etree import DocumentInvalid

from src.communication.messages_new import *


class TestClass(TestCase):
    def test_move_invalid_guid(self):
        # try to generate a message with an invalid guid (not uuid4)
        game_id = 12
        player_guid = 12
        direction = 'up'

        flag = False  # will be set to True if the message doesn't fit with the schema.
        try:
            Move(game_id, player_guid, direction)
        except DocumentInvalid:
            flag = True

        assert flag

    def test_getgames(self):
        # check if generated GetGames xml is the same as the example

        generated_xml = GetGames()
        sample_xml = open("../messages/GetGames.xml").read()

        flag = generated_xml == sample_xml
        if not flag:
            print("Generated:\n" + generated_xml)
            print("Sample:\n" + sample_xml)

        assert flag
