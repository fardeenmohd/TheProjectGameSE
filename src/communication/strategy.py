import random

from src.communication.info import GameInfo, Allegiance, Direction, GoalFieldType
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


def StrategyFactory(team: str, player_type: str, location: tuple, game_info: GameInfo):
    if team == Allegiance.RED.value:
        return BasicRedStrategy(team, player_type, location, game_info)
    else:
        return BasicBlueStrategy(team, player_type, location, game_info)


class BaseStrategy:
    def __init__(self, team: str, player_type: str, location: tuple, game_info: GameInfo):

        self.team = team
        self.player_type = player_type
        self.current_location = location
        self.game_info = game_info
        self.last_move = Decision(Decision.NULLDECISION)
        self.have_piece = "-1"  # by default, the player doesn't have a piece.
        # if self.have_piece is different from -1, then it is the id of the currently held piece

    def get_next_move(self, new_location: tuple):
        # THE MAIN STRATEGY METHOD
        self.current_location = new_location

        if self.last_move.choice == Decision.PICK_UP and self.have_piece == "-1":
            choice = self.get_random_move()
            self.last_move = choice
            return choice

        # if we have a piece, we should try to place it if we're in our goal fields.
        if self.have_piece != "-1":
            if self.game_info.is_goal_field(self.current_location):
                choice = self.try_and_place()
            else:
                choice = self.go_to_goal_fields()

        elif self.game_info.is_goal_field(self.current_location):

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
        field = self.game_info.goal_fields[self.current_location[0], self.current_location[1]]

        if field.type == GoalFieldType.UNKNOWN.value:
            # we can safely place the piece! and remove it from self.
            self.game_info.pieces[self.have_piece].player_id = "-1"
            self.have_piece = "-1"
            return Decision(Decision.PLACE)
        else:
            # our field was already discovered as a goal. let's look for a different one.
            neighbours = self.game_info.get_neighbours(self.current_location)
            for neighbour in neighbours.values():
                if self.game_info.is_goal_field(neighbour.location) and neighbour.type == GoalFieldType.UNKNOWN.value:
                    return Decision(Decision.MOVE, self.get_direction_to(neighbour))
            # no good neighbour found. we have to look for a different field to put our piece:
            return self.look_for_unknown_goal()

    def look_for_unknown_goal(self):
        # we can't place the piece on our field, all our neighbours are no good as well.
        # we need to move somewhere to find a different unknown goal.

        # base implementation: random.
        return self.get_random_move()

    def have_sufficient_information(self):
        # do we have enough information to make a clever move?

        # base implementation: return False every other move.
        return self.last_move.choice == Decision.DISCOVER

    def gather_information(self):
        # collect information, be it through Discover, or through KnowledgeExchange

        # base implementation: simply Discover
        return Decision(Decision.DISCOVER)

    def make_educated_move(self):
        # we assume we're in TaskField Area, without a piece and we have sufficient knowledge to make a clever move.

        # base implementation: move to the nearest piece.
        return self.move_toward_piece()

    def move_toward_piece(self):

        # we definitely should be in task fields:
        if not self.game_info.is_task_field(self.current_location):
            raise StrategicError(
                "Player should be in a Task Field, but wasn't! Location: " + str(self.current_location))

        # check if our current field has a piece:
        field = self.game_info.task_fields[self.current_location[0], self.current_location[1]]
        if field.has_piece:
            return Decision(Decision.PICK_UP)

        else:
            # look for the best valid (unoccupied, in-bounds) neighbour
            neighbours = self.game_info.get_neighbours(self.current_location)
            min_distance, min_neighbour = None, None
            for neighbour in neighbours.values():
                if not neighbour.is_occupied and not self.game_info.is_goal_field(neighbour.location):
                    distance = neighbour.distance_to_piece
                    # if distance is -1 or None, then there is no piece on the board at all?! better set it to 1000 just in case.
                    if distance == -1 or distance is None:
                        distance = 1000
                    if min_distance is None:
                        min_distance, min_neighbour = distance, neighbour
                    elif distance <= min_distance:
                        min_distance, min_neighbour = distance, neighbour

            return Decision(Decision.MOVE, self.get_direction_to(min_neighbour))

    def get_random_move(self, illegal=None):
        # returns a random valid move based on the current position.
        # the illegal parameter specifies a list of Directions which will be omitted from randomization.

        neighbours = self.game_info.get_neighbours(self.current_location)
        valid_directions = []
        for neighbour in neighbours.values():
            # if not neighbour.is_occupied and not self.game_info.is_out_of_bounds(neighbour):
            if neighbour[1] > self.current_location[1]:
                valid_directions.append(Direction.UP.value)
            if neighbour[1] < self.current_location[1]:
                valid_directions.append(Direction.DOWN.value)
            if neighbour[0] < self.current_location[0]:
                valid_directions.append(Direction.LEFT.value)
            if neighbour[0] > self.current_location[0]:
                valid_directions.append(Direction.RIGHT.value)
        if illegal is not None:
            # remove moves marked as 'illegal' from the list of valid moves.
            valid_directions = list(set(valid_directions) - set(illegal))
            # TODO: fix the bug that occurs here: valid_directions is sometimes empty causing program to crash.
        return Decision(Decision.MOVE, random.choice(valid_directions))

    def get_direction_to(self, field):
        # returns a Direction which should be taken in order to get to the specified field.
        if field is not None:
            y_delta = field[1] - self.current_location[1]
            x_delta = field[0] - self.current_location[0]

            if abs(y_delta) > abs(x_delta) and y_delta > 0:
                return Direction.UP.value
            elif abs(y_delta) > abs(x_delta) and y_delta < 0:
                return Direction.DOWN.value
            elif abs(y_delta) < abs(x_delta) and x_delta > 0:
                return Direction.RIGHT.value
            elif abs(y_delta) < abs(x_delta) and x_delta < 0:
                return Direction.LEFT.value
        else:
            if self.last_move.additional_info == Direction.UP.value:
                return Direction.LEFT.value
            if self.last_move.additional_info == Direction.DOWN.value:
                return Direction.RIGHT.value
            else:
                return Direction.DOWN.value

    def try_go_down(self):
        # check if the field below us is occupied:
        new_location = (self.current_location[0], self.current_location[1] - 1)
        if self.game_info.is_out_of_bounds(new_location):
            return self.get_random_move(illegal=Direction.DOWN.value)
        if self.game_info.is_goal_field(new_location):
            if not self.game_info.goal_fields[new_location].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.DOWN.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move(illegal=Direction.DOWN.value)
        else:
            if not self.game_info.task_fields[new_location].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.DOWN.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move(illegal=Direction.DOWN.value)

    def try_go_up(self):
        # check if the field above us is occupied:
        new_location = self.current_location[0], self.current_location[1] + 1
        if self.game_info.is_out_of_bounds(new_location):
            return self.get_random_move(illegal=Direction.UP.value)
        if self.game_info.is_goal_field(new_location):
            if not self.game_info.goal_fields[new_location].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.UP.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move(illegal=Direction.UP.value)
        else:
            if not self.game_info.task_fields[new_location].is_occupied:
                # we can move there
                return Decision(Decision.MOVE, Direction.UP.value)
            else:
                # we can't move there. let's move randomly.
                return self.get_random_move(illegal=Direction.UP.value)


class BasicBlueStrategy(BaseStrategy):
    def __init__(self, team: str, player_type: str, location: tuple, game_info: GameInfo):
        super(BasicBlueStrategy, self).__init__(team, player_type, location, game_info)

    def go_to_goal_fields(self):
        # goal fields are at the bottom of the board for blue players.
        return self.try_go_down()

    def go_to_task_fields(self):
        # vice versa!
        return self.try_go_up()

    def try_go_up(self):
        # overriding the base method to make sure that a Blue player doesn't get into Red goal fields.
        if self.game_info.is_task_field(self.current_location):
            if self.game_info.is_goal_field((self.current_location[0], self.current_location[1] + 1)):
                # it's red team's goal fields! we can't go there.
                return self.get_random_move(illegal=[Direction.UP.value])
        return super(BasicBlueStrategy, self).try_go_up()


class BasicRedStrategy(BaseStrategy):
    def __init__(self, team: str, player_type: str, location: tuple, game_info: GameInfo):
        super(BasicRedStrategy, self).__init__(team, player_type, location, game_info)

    def go_to_goal_fields(self):
        # goal fields are at the top of the board for red players
        return self.try_go_up()

    def go_to_task_fields(self):
        return self.try_go_down()

    def try_go_down(self):
        # overriding the base method to make sure that a Red player doesn't get into Blue goal fields.
        if self.game_info.is_task_field(self.current_location):
            if self.game_info.is_goal_field((self.current_location[0], self.current_location[1] - 1)):
                # it's red team's goal fields! we can't go there.
                return self.get_random_move(illegal=[Direction.DOWN.value])
        return super(BasicRedStrategy, self).try_go_down()
