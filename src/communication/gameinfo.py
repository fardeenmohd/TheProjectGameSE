from enum import Enum


# from datetime import datetime


class Allegiance(Enum):
    RED = 'R'
    BLUE = 'B'
    NEUTRAL = "N"


class PieceType(Enum):
    SHAM = 'S'
    LEGIT = 'L'
    UNKNOWN = 'U'


class FieldInfo:
    # Maybe default values are not necessary here but I'm just testing the class
    def __init__(self, x=0, y=0, timestamp='', distance_to_piece=1,
                 allegiance=Allegiance.NEUTRAL, is_goal_field=False, player_id=-1, piece_id=-1):
        self.x = x
        self.y = y
        self.timestamp = timestamp
        self.distance_to_piece = distance_to_piece
        self.allegiance = allegiance
        self.is_goal_field = is_goal_field
        self.player_id = player_id
        self.piece_id = piece_id


class PieceInfo:
    def __init__(self, id=-1, timestamp='', piece_type=PieceType.LEGIT):
        self.id = id
        self.timestamp = timestamp
        self.piece_type = piece_type


class GameInfo:
    def __init__(self, field_infos, player_infos, task_width, task_height, goals_height, my_x, my_y):
        # TODO maybe add game id here as well?
        self.field_infos = field_infos
        self.player_infos = player_infos
        self.task_width = task_width
        self.task_height = task_height
        self.goals_height = goals_height
        self.my_x = my_x
        self.my_y = my_y
