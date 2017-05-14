from unittest import TestCase

from src.communication import strategy
from src.communication.info import GameInfo, Allegiance, Direction, GoalFieldType, PieceInfo, PieceType
from src.communication.strategy import Decision

print("Lookup: NULLDECISION = 0, MOVE = 1, DISCOVER = 5, KNOWLEDGE_EXCHANGE = 6, PICK_UP = 7, PLACE = 8")


class TestStrategy(TestCase):
    def setUp(self):
        # carefully set up a 2x4 board
        # please make sure that whatever you're doing is very correct if you want to change anything here

        self.game_info = GameInfo(board_width=2, task_height=2, goals_height=1)
        self.game_info.initialize_fields()

        self.mock_strategy = strategy.StrategyFactory(Allegiance.RED.value, game_info=self.game_info)
        print()

    def test_first_decision(self):
        # player is in his goal field, the returned move should be DOWN.
        starting_location = (0, 3)  # this is a Red goal field.
        print("Testing first decision. Excpecting player to move down.")
        decision = self.mock_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.MOVE and decision.additional_info == Direction.DOWN.value

    def test_gather_information(self):
        # player is in a task field, move should be to gather information
        starting_location = (0, 2)  # this is a task field.
        print("Testing gather information. Excpecting player to Discover.")
        decision = self.mock_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.DISCOVER

    def test_move_toward_piece(self):
        # player is in a task field with current information, choice should be to move
        self.game_info.add_piece("1", 1, 1)
        starting_location = (0, 2)  # this is a task field.
        self.mock_strategy.last_move = Decision(Decision.DISCOVER)
        print("Testing moving to piece. Expecting player to Move (to a piece).")
        decision = self.mock_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.MOVE

    def test_valid_pickup(self):
        self.game_info.add_piece("1", 0, 2)  # adding a piece
        starting_location = (0, 2)  # this is a task field
        self.mock_strategy.last_move = Decision(Decision.DISCOVER)
        print("Testing picking a piece. Expecting player to Pick(a piece).")
        decision = self.mock_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.PICK_UP

    def test_valid_place(self):
        self.game_info.pieces["1"] = PieceInfo("1", PieceType.NORMAL, "1")
        starting_location = (0, 0)
        self.mock_strategy.have_piece = "1"
        self.game_info.goal_fields[0, 0].type = GoalFieldType.GOAL.value
        self.mock_strategy.last_move = Decision(Decision.DISCOVER)
        print("Testing placing a piece. Expecting player to Place(a piece).")
        decision = self.mock_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.PLACE




