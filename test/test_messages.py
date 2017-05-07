import uuid
from unittest import TestCase

from lxml.etree import DocumentInvalid

from src.communication.info import *
from src.communication.messages import *


class TestClass(TestCase):
    def test_getgames(self):
        # check if generated GetGames xml is the same as the example

        generated_xml = GetGames()
        sample_xml = open("../messages/GetGames.xml").read()

        flag = generated_xml == sample_xml
        if not flag:
            print("Generated:\n" + generated_xml)
            print("Sample:\n" + sample_xml)

        assert flag

    def test_move_valid(self):
        game_id = "1"
        player_guid = str(uuid.uuid4())
        direction = Direction.UP.value

        flag = True
        try:
            Move(game_id, player_guid, direction)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_move_invalid(self):
        game_id = 0
        player_guid = 0
        direction = Direction.DOWN.value

        flag = False
        try:
            Move(game_id, player_guid, direction)
        except DocumentInvalid:
            flag = True
        assert flag

    def test_pickup_valid(self):
        game_id = "1"
        player_guid = str(uuid.uuid4())

        flag = True
        try:
            PickUpPiece(game_id, player_guid)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_pickup_invalid(self):
        game_id = 0
        player_guid = 0

        flag = False
        try:
            PickUpPiece(game_id, player_guid)
        except DocumentInvalid:
            flag = True
        assert flag

    def test_place_piece_valid(self):
        game_id = "1"
        player_guid = str(uuid.uuid4())

        flag = True
        try:
            PlacePiece(game_id, player_guid)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_place_piece_invalid(self):
        game_id = 0
        player_guid = 0

        flag = False
        try:
            PlacePiece(game_id, player_guid)
        except DocumentInvalid:
            flag = True
        assert flag

    def test_discover_valid(self):
        game_id = "1"
        player_guid = str(uuid.uuid4())

        flag = True
        try:
            Discover(game_id, player_guid)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_discover_invalid(self):
        game_id = 0
        player_guid = 0

        flag = False
        try:
            Discover(game_id, player_guid)
        except DocumentInvalid:
            flag = True

        assert flag

    def test_authorize_knowledge_valid(self):
        game_id = "1"
        player_guid = str(uuid.uuid4())
        with_player_id = "2"
        flag = True
        try:
            AuthorizeKnowledgeExchange(game_id, player_guid, with_player_id)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_authorize_knowledge_invalid(self):
        game_id = 0
        player_guid = 0
        with_player_id = 0
        flag = False
        try:
            AuthorizeKnowledgeExchange(game_id, player_guid, with_player_id)
        except DocumentInvalid:
            flag = True

        assert flag

    def test_game_valid(self):
        player_id = "1"
        another_player_id = "2"
        teams = {Allegiance.RED.value: {
            player_id: PlayerInfo(player_id,
                                  team=Allegiance.RED.value,
                                  type=PlayerType.LEADER.value)},
            Allegiance.BLUE.value: {
                another_player_id: PlayerInfo(another_player_id,
                                              team=Allegiance.BLUE.value,
                                              type=PlayerType.LEADER.value)}}
        board_width = 3
        tasks_height = 3
        goals_height = 3
        player_location = (1, 1)

        flag = True
        try:
            Game(player_id, teams, board_width, tasks_height, goals_height, player_location)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_game_invalid(self):
        player_id = 0
        another_player_id = 0
        teams = {}
        board_width = 3
        tasks_height = 3
        goals_height = 3
        player_location = (1, 1)

        flag = False
        try:
            Game(player_id, teams, board_width, tasks_height, goals_height, player_location)
        except DocumentInvalid:
            flag = True

        assert flag

    def test_knowledge_request_valid(self):
        player_id = "1"
        sender_id = "2"

        flag = True
        try:
            KnowledgeExchangeRequest(player_id, sender_id)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_knowledge_request_invalid(self):
        player_id = 1
        sender_id = 2

        flag = False
        try:
            KnowledgeExchangeRequest(player_id, sender_id)
        except DocumentInvalid:
            flag = True
        except TypeError:
            flag = True

        assert flag

    def test_knowledge_accept_valid(self):
        player_id = "1"
        sender_id = "2"

        flag = True
        try:
            AcceptExchangeRequest(player_id, sender_id)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_knowledge_accept_invalid(self):
        player_id = 1
        sender_id = 2

        flag = True
        try:
            AcceptExchangeRequest(player_id, sender_id)
        except DocumentInvalid:
            flag = False
        except TypeError:
            flag = True

        assert flag

    def test_knowledge_reject_valid(self):
        player_id = "1"
        sender_id = "2"

        flag = True
        try:
            RejectKnowledgeExchange(player_id, sender_id, flag)
        except DocumentInvalid:
            flag = False

        assert flag

    def test_knowledge_reject_invalid(self):
        player_id = 1
        sender_id = 2

        flag = False
        try:
            RejectKnowledgeExchange(player_id, sender_id, flag)
        except DocumentInvalid:
            flag = True
        except TypeError:
            flag = True

        assert flag

    def test_register_games_valid(self):
        game_name = "easy peasy"
        blue_team_players = 5
        red_team_players = 5

        flag = True
        try:
            RegisterGame(game_name, blue_team_players, red_team_players)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_register_games_invalid(self):
        game_name = 13414
        blue_team_players = 5
        red_team_players = 5

        flag = False
        try:
            RegisterGame(game_name, blue_team_players, red_team_players)

        except DocumentInvalid:
            flag = True
        except TypeError:
            flag = True

        assert flag

    def test_confirm_register_valid(self):
        game_id = "1"

        flag = True
        try:
            ConfirmGameRegistration(game_id)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_confirm_register_invalid(self):
        game_id = "a"

        flag = False
        try:
            ConfirmGameRegistration(game_id)

        except DocumentInvalid:
            flag = True

        except TypeError:
            flag = True

        assert flag

    def test_reject_register_valid(self):
        game_name = "easy peasy"

        flag = True
        try:
            RejectGameRegistration(game_name)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_game_started(self):
        game_id = "1"

        flag = True
        try:
            GameStarted(game_id)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_registered_games(self):
        task_fields = {(1, 1): TaskFieldInfo(1, 1)}
        goal_fields = {(2, 2): TaskFieldInfo(2, 2)}
        pieces = {"1": PieceInfo("1", location=(2, 3))}

        games = {"1": GameInfo("1", "easy peasy", task_fields, goal_fields, pieces, 4, 4, 4, 1, 1, True, False, "1",
                               datetime.now())}

        flag = True
        try:
            RegisteredGames(games)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_join_game(self):
        game_name = "easy peasy"
        pref_team = Allegiance.RED.value
        pref_type = PlayerType.LEADER.value
        player_id = "1"

        flag = True
        try:
            JoinGame(game_name, pref_team, pref_type, player_id)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_confirm_joining_game(self):
        player_id = "1"
        game_id = "1"
        player_guid = uuid.uuid4()
        team = Allegiance.RED.value
        type = PlayerType.LEADER.value

        flag = True
        try:
            ConfirmJoiningGame(player_id, game_id, player_guid, team, type)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_reject_joining_game(self):
        player_id = "1"
        game_name = "easy peasy"

        flag = True
        try:
            RejectJoiningGame(player_id, game_name)

        except DocumentInvalid:
            flag = False

        assert flag

    def test_gm_disconnected(self):
        game_id = "1"

        flag = True
        try:
            GameMasterDisconnected(game_id)

        except DocumentInvalid:
            flag = False

        assert flag
    def test_playa_disconnected(self):
        player_id = "1"

        flag = True
        try:
            GameMasterDisconnected(player_id)

        except DocumentInvalid:
            flag = False