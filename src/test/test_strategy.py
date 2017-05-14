import uuid
from unittest import TestCase
import random

from lxml.etree import DocumentInvalid
from src.communication.info import *
from src.communication.messages import *
from src.communication import strategy
from src.communication.info import GameInfo, Allegiance, Direction, GoalFieldType

location = (1, 1)
location2 = (1, 2)
location3 = (0, 2)
task_fields = {(1, 1): TaskFieldInfo(1, 1)}
goal_fields = {(2, 2): TaskFieldInfo(2, 2)}
pieces = {"1": PieceInfo("1", location=(2, 3))}
game_info = GameInfo("1", "easy peasy", task_fields, goal_fields, pieces, 4, 4, 4, 1, 1, True, False, "1",
                     datetime.now())

class TestStrategy(TestCase):
    def test_decision(self):
        flag = True
        try:
            self.decision = strategy.Decision(5)
        except DocumentInvalid:
            flag = False
        assert flag

    def test_no_decision(self):
        flag = True
        try:
            self.decision = strategy.Decision(5)
        except DocumentInvalid:
            flag = False
        assert flag


class TestBaseStrategy(TestCase):
    def setUp(self):
        self.mock_strategy = strategy.BaseStrategy(Allegiance.RED.value, PlayerType.MEMBER.value, location, game_info)

    def test_base_decision(self):
        flag = True
        try:
            self.mock_strategy = strategy.BaseStrategy(Allegiance.RED.value, PlayerType.MEMBER.value, location, game_info)
        except DocumentInvalid:
            flag = False
        assert flag

    def test_gather_information(self):
        flag = True
        try:
            self.mock_strategy.get_next_move(location2)
        except DocumentInvalid:
            flag = False
        assert flag

    def test_move_toward_piece(self):
        self.decision = strategy.Decision(5)
        flag = True
        try:
            self.mock_strategy.move_toward_piece()
        except DocumentInvalid:
            flag = False
        assert flag

    def test_move_toward_piece_not_in_task_field(self):
        self.decision = strategy.Decision(5)
        self.mock_strategy = strategy.BaseStrategy(Allegiance.RED.value, PlayerType.MEMBER.value, location3, game_info)

        flag = False
        try:
            self.mock_strategy.move_toward_piece()
        except DocumentInvalid:
            flag = True
        assert flag


