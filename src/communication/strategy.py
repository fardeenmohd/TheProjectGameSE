import random

from src.communication.info import GameInfo, Allegiance, Location, Direction, GoalFieldType
from src.communication.unexpected import StrategicError


class Decision:
    def __init__(self, choice: int, additional_info=None):
        self.choice = choice
        self.additional_info = additional_info

    NULLDECISION = 0
    MOVE = 1
    DISCOVER = 5
    KNOWLEDGE_EXCHANGE = 6
    PICK_UP = 7
    PLACE = 8


def StrategyFactory(team: str, player_type: str, location: Location, game_info: GameInfo):
    if team == Allegiance.RED.value:
        return BasicRedStrategy(team, player_type, location, game_info)
    else:
        return BasicBlueStrategy(team, player_type, location, game_info)


class BaseStrategy:
    def __init__(self, team: str, player_type: str, location: Location, game_info: GameInfo):

        self.team = team
        self.player_type = player_type
        self.current_location = location
        self.game_info = game_info
        self.last_move = None
        self.have_piece = -1  # by default, the player doesn't have a piece.
        # if self.have_piece is different from -1, then it is the id of the currently held piece

    def get_next_move(self):
        # THE MAIN STRATEGY METHOD

        # if we have a piece, we should try to place it if we're in our goal fields.
        if self.have_piece > -1:
            if self.game_info.is_goal_field(self.current_location):
                choice = self.try_and_place()
            else:
                choice = self.go_to_goal_fields()

        elif self.game_info.is_task_field(self.current_location):
            # we do not have a piece. let's go to task fields to collect one.
            choice = self.go_to_task_fields()

        else:
            # we're in Task Field area. do we have enough information to make a clever move?
            if not self.have_sufficient_information():
                choice = self.gather_information()
            else:
                choice = self.make_educated_move()

        self.last_move = choice
        return choice

    def go_to_goal_fields(self):
        # abstract. implementation depends on if we're red or blue.
        raise NotImplementedError

    def go_to_task_fields(self):
        # abstract. implementation depends on if we're red or blue.
        raise NotImplementedError

    def try_and_place(self):
        # try to place the piece on the field on which we're standing.

        # first find if our would-be goal field is not already discovered:
        field = self.game_info.goal_fields[self.current_location.x, self.current_location.y]
        if field.type == GoalFieldType.UNKNOWN:
            return Decision(Decision.PLACE)
        else:
            # our field was already discovered as a goal. let's look for a different one.
            neighbours = self.game_info.get_neighbours(self.current_location)
            for neighbour in neighbours.values():
                if neighbour.type == GoalFieldType.UNKNOWN:
                    good_neighbour = neighbour
                    break
            else:
                # no good neighbour found. we have to look for a different field to put our piece:
                return self.look_for_empty_goal()
            return Decision(Decision.MOVE, self.get_direction_to(good_neighbour))

    def look_for_empty_goal(self):
        # we can't place the piece on our field, all our neighbours are no good as well.
        # we need to move somewhere to find a different unknown goal.

        # base implementation: random.
        move_direction = self.get_random_move()
        return Decision(Decision.MOVE, move_direction)

    def have_sufficient_information(self):
        # do we have enough information to make a clever move?

        # base implementation: return False every other move.
        return self.last_move.choice == Decision.DISCOVER

    def gather_information(self):
        # collect information, be it through Discover, or through KnowledgeExchange

        # base implementation: simply Discover
        return Decision(Decision.DISCOVER)

    def make_educated_move(self):
        # we assume we're in Task Field Area, without a piece and that we have sufficient knowledge to make a clever move.

        # base implementation: move to the nearest piece.
        return self.move_toward_piece()

    def move_toward_piece(self):

        # we definitely should be in task fields:
        if self.game_info.is_task_field(self.current_location):
            raise StrategicError(
                "Player should be in a Task Field, but wasn't! Location: " + str(self.current_location))

        # check if our current field has a piece:
        field = self.game_info.task_fields[self.current_location.x, self.current_location.y]
        if field.has_piece():
            self.have_piece = field.piece_id
            return Decision(Decision.PICK_UP)

        else:
            # look for the best valid (unoccupied, in-bounds) neighbour
            neighbours = self.game_info.get_neighbours(self.current_location)
            min_distance, min_neighbour = None, None
            for neighbour in neighbours.values():
                if not neighbour.is_occupied:
                    distance = neighbour.distance_to_piece
                    if min_distance is None or distance <= min_distance:
                        min_distance, min_neighbour = distance, neighbour

            return Decision(Decision.MOVE, self.get_direction_to(min_neighbour))

    def get_random_move(self):
        # returns a random valid move based on the current position.

        neighbours = self.game_info.get_neighbours(self.current_location)
        valid_directions = []
        for neighbour in neighbours.values():
            if not neighbour.is_occupied:
                if neighbour.y > self.current_location.y:
                    valid_directions.append(Direction.UP.value)
                if neighbour.y < self.current_location.y:
                    valid_directions.append(Direction.DOWN.value)
                if neighbour.x < self.current_location.x:
                    valid_directions.append(Direction.LEFT.value)
                if neighbour.x > self.current_location.x:
                    valid_directions.append(Direction.RIGHT.value)
        return random.choice(valid_directions)

    def get_direction_to(self, field):
        # returns a Direction which should be taken in order to get to the specified field.

        y_delta = field.y - self.current_location.y
        x_delta = field.x - self.current_location.x

        if abs(y_delta) > abs(x_delta) and y_delta > 0:
            return Direction.UP.value
        if abs(y_delta) > abs(x_delta) and y_delta < 0:
            return Direction.DOWN.value
        if abs(y_delta) < abs(x_delta) and x_delta > 0:
            return Direction.RIGHT.value
        if abs(y_delta) < abs(x_delta) and x_delta < 0:
            return Direction.LEFT.value

    def try_go_down(self):
        # check if the field below us is occupied:
        if self.game_info.is_goal_field(Location(self.current_location.x, self.current_location.y - 1)):
            if not self.game_info.goal_fields[self.current_location.x, self.current_location.y - 1].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.DOWN.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move()
        else:
            if not self.game_info.task_fields[self.current_location.x, self.current_location.y - 1].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.DOWN.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move()

    def try_go_up(self):
        # check if the field above us is occupied:
        if self.game_info.is_goal_field(Location(self.current_location.x, self.current_location.y + 1)):
            if not self.game_info.goal_fields[self.current_location.x, self.current_location.y + 1].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.UP.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move()
        else:
            if not self.game_info.task_fields[self.current_location.x, self.current_location.y + 1].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.UP.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move()


class BasicBlueStrategy(BaseStrategy):
    def __init__(self, team: str, player_type: str, location: Location, game_info: GameInfo):
        super(BasicBlueStrategy, self).__init__(team, player_type, location, game_info)

    def go_to_goal_fields(self):
        # goal fields are at the bottom of the board for blue players.
        return self.try_go_down()

    def go_to_task_fields(self):
        # vice versa!
        return self.try_go_up()


class BasicRedStrategy(BaseStrategy):
    def __init__(self, team: str, player_type: str, location: Location, game_info: GameInfo):
        super(BasicRedStrategy, self).__init__(team, player_type, location, game_info)

    def go_to_goal_fields(self):
        # goal fields are at the top of the board for red players
        return self.try_go_up()

    def go_to_task_fields(self):
        return self.try_go_down()
