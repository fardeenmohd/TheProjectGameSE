from datetime import datetime
from enum import Enum


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
    def __init__(self, x=0, y=0, timestamp=datetime.now(), player_id=None):
        self.x = x
        self.y = y
        self.timestamp = timestamp
        self.player_id = -1
        if player_id is not None:
            self.player_id = player_id

    def is_occupied(self):
        return self.player_id != -1


class TaskFieldInfo(FieldInfo):
    # Maybe default values are not necessary here but I'm just testing the class
    def __init__(self, x=0, y=0, timestamp=datetime.now(), distance_to_piece=-1, player_id=None, piece_id=None):
        super(TaskFieldInfo, self).__init__(x, y, timestamp, player_id)
        self.distance_to_piece = distance_to_piece
        self.piece_id = piece_id

    def has_piece(self):
        return self.piece_id != -1


class GoalFieldInfo(FieldInfo):
    def __init__(self, x=0, y=0, allegiance=Allegiance.NEUTRAL, player_id=None, timestamp=datetime.now(),
                 type=GoalFieldType.UNKNOWN):
        super(GoalFieldInfo, self).__init__(x, y, timestamp, player_id)
        self.allegiance = allegiance
        self.type = type


class PieceInfo:
    def __init__(self, id=-1, timestamp=datetime.now(), piece_type=PieceType.NORMAL, player_id=None):
        self.id = id
        self.timestamp = timestamp
        self.piece_type = piece_type
        self.player_id = player_id


class ClientInfo:
    """might not actually be used that much, encapsulate some information about client id, their type etc."""

    def __init__(self, id="-1", tag=ClientTypeTag.CLIENT, socket=None, game_name="", game_master_id="-1"):
        self.id = id
        self.tag = tag
        self.socket = socket
        self.game_name = game_name
        self.game_master_id = game_master_id

    def get_tag(self):
        return self.tag.value + str(self.id)


class GameInfo:
    def __init__(self, id=-1, name="", task_fields=None, goal_fields=None, pieces=None, board_width=0, task_height=0,
                 goals_height=0, max_blue_players=0, max_red_players=0, open=True, finished=False, game_master_id=""):
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
        self.pieces = pieces
        self.goal_fields = goal_fields
        self.task_fields = task_fields
        self.board_width = board_width
        self.task_height = task_height
        self.goals_height = goals_height

        self.teams = {Allegiance.RED.value: {}, Allegiance.BLUE.value: {}}
        # self.teams is a dict of dicts: team => {player_id => PlayerInfo}

        self.max_blue_players = max_blue_players
        self.max_red_players = max_red_players

    def check_for_empty_task_fields(self):
        for task_field in self.task_fields.values():
            if task_field.piece_id == -1:
                return True

        return False

    def has_piece(self, x, y):
        if (x, y) in self.task_fields.keys():
            return self.task_fields[x, y].has_piece()
        else:
            return False

    def is_task_field(self, location):
        return location in self.task_fields.keys()

    def is_goal_field(self,location):
        return location in self.goal_fields.keys()

    def is_out_of_bounds(self,location):
        return not (self.is_task_field() or self.is_goal_field())

class PlayerInfo(ClientInfo):
    """used by GameMaster only (for now, at least...)"""

    def __init__(self, id="-1", tag=PlayerType.MEMBER.value, team=None, info: GameInfo = None,
                 location: tuple = None, guid=None):
        super(PlayerInfo, self).__init__(id=id, tag=ClientTypeTag.PLAYER)
        self.type = tag
        self.info = info
        self.team = team
        self.location = location
        self.guid = guid
