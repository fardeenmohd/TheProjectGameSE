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


class TaskFieldInfo:
	# Maybe default values are not necessary here but I'm just testing the class
	def __init__(self, x = 0, y = 0, timestamp = '', distance_to_piece = 1, player_id = -1, piece_id = -1):
		self.x = x
		self.y = y
		self.timestamp = timestamp
		self.distance_to_piece = distance_to_piece
		self.player_id = player_id
		self.piece_id = piece_id

	def has_piece(self):
		return self.piece_id != -1

	def is_occupied(self):
		return self.player_id != -1


class GoalFieldInfo:
	def __init__(self, x = 0, y = 0, allegiance = Allegiance.NEUTRAL, player_id = -1, timestamp = ''):
		self.y = y
		self.allegiance = allegiance
		self.player_id = player_id
		self.timestamp = timestamp


class PieceInfo:
	def __init__(self, id = -1, timestamp = '', piece_type = PieceType.LEGIT):
		self.id = id
		self.timestamp = timestamp
		self.piece_type = piece_type


class GameInfo:
	def __init__(self, pieces = None, task_fields = None, goal_fields = None, player_infos = None, board_width = 0,
	             task_height = 0, goals_height = 0):
		# TODO maybe add game id here as well?
		# TODO: convert goal_fields and task_fields and pieces into dicts.

		if pieces is None:
			pieces = {}
		if goal_fields is None:
			goal_fields = []
		if task_fields is None:
			task_fields = {}
		if player_infos is None:
			player_infos = []
		self.pieces = pieces
		self.goal_fields = goal_fields
		self.task_fields = task_fields
		self.player_infos = player_infos
		self.board_width = board_width
		self.task_height = task_height
		self.goals_height = goals_height

	def check_for_empty_fields(self):
		for task_field in self.task_fields.values():
			if task_field.piece_id == -1:
				return True

		return False

	def has_piece(self, x, y):
		if (x, y) in self.task_fields.keys():
			return self.task_fields[x, y].has_piece()
		else: return False
