from unittest import TestCase

from src.communication import strategy
from src.communication.info import GameInfo, Allegiance, Direction, GoalFieldType, PieceInfo, PieceType
from src.communication.strategy import Decision

print("Lookup: NULLDECISION = 0, MOVE = 1, DISCOVER = 5, KNOWLEDGE_EXCHANGE = 6, PICK_UP = 7, PLACE = 8 \n")
# carefully set up a 2x4 board
# please make sure that whatever you're doing is very correct if you want to change anything here
BOARD_WIDTH = 2
TASK_HEIGHT = 2
GOALS_HEIGHT = 1
FULL_HEIGHT = 2 * GOALS_HEIGHT + TASK_HEIGHT

print("Miniature Board:")
for y in range(FULL_HEIGHT):
    symbol = '  T'
    if y >= 0 and (y < GOALS_HEIGHT):
        symbol = '  R'
    if y >= FULL_HEIGHT - GOALS_HEIGHT:
        symbol = '  B'
    print(str(y) + 2 * symbol, sep=' ', end='\n', flush=True)


class TestStrategy(TestCase):
    def setUp(self):
        # setting basic game info for both team strategies
        self.game_info = GameInfo(board_width=BOARD_WIDTH, task_height=TASK_HEIGHT, goals_height=GOALS_HEIGHT)
        self.game_info.initialize_fields()
        self.red_strategy = strategy.StrategyFactory(Allegiance.RED.value, game_info=self.game_info)
        self.blue_strategy = strategy.StrategyFactory(Allegiance.BLUE.value, game_info=self.game_info)
        print()

    def test_first_decision(self):
        # player is in his goal field, the returned move should be DOWN.
        starting_location = (0, 3)  # this is a Red goal field.
        print("Testing first decision. Excpecting player to move down.")
        decision = self.red_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.MOVE and decision.additional_info == Direction.DOWN.value

    def test_gather_information(self):
        # player is in a task field, move should be to gather information
        starting_location = (0, 2)  # this is a task field.
        print("Testing gather information. Excpecting player to Discover.")
        decision = self.red_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.DISCOVER

    def test_move_toward_piece(self):
        # player is in a task field with current information, choice should be to move
        self.game_info.add_piece("1", 0, 2)
        starting_location = (0, 1)  # this is a task field.
        self.red_strategy.last_move = Decision(Decision.DISCOVER)
        print("Testing moving to piece. Expecting player to Move (to a piece).")
        decision = self.red_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.additional_info == Direction.UP.value

    def test_valid_pickup(self):
        self.game_info.add_piece("1", 0, 2)  # adding a piece
        starting_location = (0, 2)  # this is a task field
        self.red_strategy.last_move = Decision(Decision.DISCOVER)
        print("Testing picking a piece. Expecting player to Pick(a piece).")
        decision = self.red_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.PICK_UP

    def test_try_to_go_to_other_team_area(self):
        self.red_strategy.current_location = (0, 1)
        self.red_strategy.last_move = Decision(Decision.DISCOVER)
        decision = self.red_strategy.try_go_down()
        print("Testing player to not move in enemy goal area")
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.additional_info != Direction.DOWN.value

    def test_try_collision(self):
        self.blue_strategy.current_location = (0, 1)
        self.red_strategy.current_location = (0, 2)
        red_decision = self.red_strategy.try_go_down()
        print("Testing the red player to not move on same task field as any other player ")
        print("Got this decision: " + str(red_decision.choice) + ", additional info: " + str(
            red_decision.additional_info))
        blue_decision = self.blue_strategy.try_go_up()
        print("Testing the blue player to not move on same task field as any other player ")
        print("Got this decision: " + str(blue_decision.choice) + ", additional info: " + str(
            blue_decision.additional_info))

        assert red_decision != blue_decision

    def test_valid_place(self):
        self.game_info.pieces["1"] = PieceInfo("1", PieceType.NORMAL)
        self.red_strategy.have_piece = "1"
        self.red_strategy.last_move = Decision(Decision.MOVE)
        starting_location = (0, 3)
        print("Testing placing a piece. Expecting player to Place(a piece).")
        decision = self.red_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.choice == Decision.PLACE

    def test_player_going_back_with_the_piece(self):
        self.game_info.pieces["1"] = PieceInfo("1", PieceType.NORMAL)
        self.red_strategy.have_piece = "1"
        self.red_strategy.last_move = Decision(Decision.PICK_UP)
        starting_location = (0, 1)
        print("Testing red player to go back up when he picks a piece")
        decision = self.red_strategy.get_next_move(starting_location)
        print("Got this decision: " + str(decision.choice) + ", additional info: " + str(decision.additional_info))
        assert decision.additional_info == Direction.UP.value
