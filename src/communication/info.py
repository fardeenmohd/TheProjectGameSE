from datetime import datetime
from enum import Enum
from queue import Queue

from src.communication.helpful_math import Manhattan_Distance as manhattan
from src.communication.unexpected import CustomBaseExceptionWithMessage, LocationOutOfBoundsError


class Location:
    # legacy class, should not be used anymore (use x,y tuples for location instead)
    def __init__(self, x, y):
        self.x = x
        self.y = y


class ClientTypeTag(Enum):
    CLIENT = "C"
    PLAYER = "P"
    LEADER = "L"
    GAME_MASTER = "GM"
    BLUE_PLAYER = "BP"
    BLUE_LEADER = "BL"
    RED_PLAYER = "RP"
    RED_LEADER = "RL"


class Direction(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    STAY = 'stay'


class Allegiance(Enum):
    RED = 'red'
    BLUE = 'blue'
    NEUTRAL = 'neutral'


class PlayerType(Enum):
    MEMBER = "member"
    LEADER = "leader"


class PieceType(Enum):
    SHAM = 'sham'
    NORMAL = 'normal'
    UNKNOWN = 'unknown'


class GoalFieldType(Enum):
    GOAL = 'goal'
    NON_GOAL = 'non-goal'
    UNKNOWN = 'unknown'


class FieldInfo:
    def __init__(self, x=0, y=0, timestamp=datetime.now(), player_id="-1"):
        self.x = x
        self.y = y
        self.timestamp = timestamp
        self.player_id = player_id

    @property
    def is_occupied(self):
        return not (self.player_id == "-1" or self.player_id is None)

    @property
    def location(self):
        return self.x, self.y

    def __setitem__(self, key, value):
        if isinstance(key, int) and isinstance(value, int):
            if key != 0 and key != 1:
                raise IndexError
            if key == 0:
                self.x = value
            if key == 1:
                self.y = value
        elif isinstance(key, tuple) and isinstance(value, tuple):
            if not isinstance(key[0], int) or not isinstance(key[1], int):
                raise KeyError
            if not isinstance(value[0], int) or not isinstance(value[1], int):
                raise KeyError
            self.__setitem__(key[0], value[0])
            self.__setitem__(key[1], value[1])
        else:
            raise TypeError

    def __getitem__(self, key):
        if key != 0 and key != 1:
            raise IndexError
        if key == 0:
            return self.x
        if key == 1:
            return self.y


class TaskFieldInfo(FieldInfo):
    # Maybe default values are not necessary here but I'm just testing the class
    def __init__(self, x=0, y=0, timestamp=datetime.now(), distance_to_piece=-1, player_id="-1", piece_id="-1"):
        super(TaskFieldInfo, self).__init__(x, y, timestamp, player_id)
        self.distance_to_piece = distance_to_piece
        self.piece_id = piece_id

    @property
    def has_piece(self) -> bool:
        return self.piece_id != "-1" and self.piece_id is not None


class GoalFieldInfo(FieldInfo):
    def __init__(self, x=0, y=0, allegiance=Allegiance.NEUTRAL.value, player_id=None, timestamp=datetime.now(),
                 type=GoalFieldType.UNKNOWN.value):
        super(GoalFieldInfo, self).__init__(x, y, timestamp, player_id)
        self.allegiance = allegiance
        self.type = type


class PieceInfo:
    def __init__(self, id="-1", type=PieceType.UNKNOWN.value, player_id="-1", location=None, timestamp=datetime.now()):
        self.id = id
        self.type = type
        self.player_id = player_id
        self.location = location
        self.timestamp = timestamp


class ClientInfo:
    """might not actually be used that much, encapsulate some information about client id, their type etc."""

    def __init__(self, id="-1", tag=ClientTypeTag.CLIENT, socket=None, game_name="", game_master_id="-1", game_id="-1"):
        self.id = id
        self.tag = tag
        self.socket = socket
        self.game_name = game_name
        self.game_id = game_id
        self.game_master_id = game_master_id
        self.queue = Queue()

    def get_tag(self):
        return self.tag.value + str(self.id)


class GameInfo:
    def __init__(self, id="-1", name="", task_fields=None, goal_fields=None, pieces=None, board_width=0, task_height=0,
                 goals_height=0, max_blue_players=0, max_red_players=0, open=True, finished=False, game_master_id="",
                 latest_timestamp=""):
        self.id = id
        self.name = name
        self.open = open
        self.finished = finished
        self.game_master_id = game_master_id
        if pieces is None:
            pieces = {}
        if goal_fields is None:
            goal_fields = {}
        if task_fields is None:
            task_fields = {}
        self.pieces = pieces  # pieceId => PieceInfo
        self.goal_fields = goal_fields  # (x,y) => GoalFieldInfo
        self.task_fields = task_fields  # (x,y) => TaskFieldInfo
        self.board_width = board_width
        self.task_height = task_height
        self.goals_height = goals_height
        self.latest_timestamp = latest_timestamp

        self.teams = {Allegiance.RED.value: {}, Allegiance.BLUE.value: {}}
        # self.teams is a dict of dicts: team => {player_id => PlayerInfo}

        self.max_blue_players = max_blue_players
        self.max_red_players = max_red_players

    def check_for_empty_task_fields(self):
        for task_field in self.task_fields.values():
            if task_field.piece_id == "-1":
                return True

        return False

    def has_piece(self, x, y):
        if (x, y) in self.task_fields.keys():
            return self.task_fields[x, y].has_piece
        else:
            raise KeyError

    def is_task_field(self, location: tuple):
        return (location[0], location[1]) in self.task_fields.keys()

    def is_goal_field(self, location: tuple):
        return (location[0], location[1]) in self.goal_fields.keys()

    def is_out_of_bounds(self, location: tuple):
        return not self.is_task_field(location) and not self.is_goal_field(location)

    def get_neighbours(self, location: tuple, look_for_extended=False):
        """
        :param look_for_extended: if True, function will look for all 8 neighbours (including diagonal) instead of 4.
        :return: dict of neighbouring fields (both Goal and Task Fields).
        """
        dist = 1
        if look_for_extended:
            dist = 2

        neighbours = {}  # (x,y) => FieldInfo
        for (x, y), field in self.task_fields.items():
            if not (abs(location[0] - x) > 1) and not abs(location[1] - y) > 1:
                if abs(location[0] - x) + abs(location[1] - y) <= dist:
                    neighbours[x, y] = field
        for (x, y), field in self.goal_fields.items():
            if not (abs(location[0] - x) > 1) and not abs(location[1] - y) > 1:
                if abs(location[0] - x) + abs(location[1] - y) <= dist:
                    neighbours[x, y] = field

        # neighbours will include the original field itself, so we remove it:
        # del neighbours[location[0], location[1]]
        return neighbours

    def update_field_distances(self):
        """
        re-calculates distance_to_piece field in all TaskFields on the board.
        """
        for field in self.task_fields.values():
            min_piece, min_dist = None, None
            for piece in [piece for piece in self.pieces.values() if piece.location is not None]:
                if piece.location == field.location:
                    min_dist = 0
                    break
                if min_dist is None:
                    min_piece, min_dist = piece, manhattan(field.location, piece.location)
                if manhattan(field.location, piece.location) <= min_dist:
                    min_piece, min_dist = piece, manhattan(field.location, piece.location)
            field.distance_to_piece = min_dist

    @staticmethod
    def fieldwise_manhattan_distance(field_a: FieldInfo, field_b: FieldInfo):
        return abs(field_a[0] - field_b[0]) + abs(field_a[1] - field_b[1])

    @property
    def whole_board_length(self):
        return 2 * self.goals_height + self.task_height - 1

    def initialize_fields(self, goals_height=None, task_height=None, board_width=None):

        if goals_height is not None:
            self.goals_height = goals_height
        if task_height is not None:
            self.task_height = task_height
        if board_width is not None:
            self.board_width = board_width

        y = 2 * self.goals_height + self.task_height - 1

        for i in range(self.goals_height):
            for x in range(self.board_width):
                if (x, y) not in self.goal_fields.keys():
                    self.goal_fields[x, y] = GoalFieldInfo(x, y, Allegiance.RED.value)
            y -= 1

        for i in range(self.task_height):
            for x in range(self.board_width):
                if (x, y) not in self.task_fields.keys():
                    self.task_fields[x, y] = TaskFieldInfo(x, y)
            y -= 1

        for i in range(self.goals_height):
            for x in range(self.board_width):
                if (x, y) not in self.goal_fields.keys():
                    self.goal_fields[x, y] = GoalFieldInfo(x, y, Allegiance.BLUE.value)
            y -= 1

    def add_piece(self, id: str, x: int, y: int, type: str = PieceType.NORMAL):

        if self.is_out_of_bounds((x, y)):
            raise LocationOutOfBoundsError(message="Can't place a piece.", location=(x, y))
        elif self.is_goal_field((x, y)):
            raise CustomBaseExceptionWithMessage(
                "Can't place a piece on location " + str((x, y)) + ". It's a goal field!")
        elif self.has_piece(x, y):
            raise CustomBaseExceptionWithMessage(
                "Can't place a piece on location " + str((x, y)) + ". Field already has a piece!")
        new_piece = PieceInfo(id, type=type, location=(x, y))
        self.task_fields[x, y].piece_id = id
        self.pieces[id] = new_piece
        # update distance_to_piece in all fields:
        self.update_field_distances()


class PlayerInfo():
    """used by GameMaster only (for now, at least...)"""

    def __init__(self, id="-1", team=None, info: GameInfo = None, type=None, location=None, guid=None, piece_id="-1"):
        self.id = id
        self.type = type
        if info is not None:
            self.info = info
        else:
            self.info = GameInfo()
        self.team = team
        self.location = location
        self.piece_id = piece_id
        self.guid = guid
