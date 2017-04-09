from src.communication.info import GameInfo, Allegiance


class BaseStrategy:
    def __init__(self, game_info: GameInfo = None, location=None, team=None):
        self.has_piece = 0  # player has not piece
        self.game_info = game_info
        self.location = location
        self.team = team

    def get_next_move(self):
        if not self.has_piece:
            self.move_player_to_task_field_area()
        else:
            if self.team is Allegiance.BLUE.value:
                return "up"
            else:
                return "down"

    def move_player_to_task_field_area(self):
        if self.location[1] < self.game_info.goals_height:  # blue team area
            # check if upper field is occupied then go left or right and check if it is on the board
            return 'up'

        elif self.location[1] < self.game_info.goals_height + self.game_info.task_height:  # in the task field
            self.move_toward_piece()  # logic of the player being on the task field

        else:  # red team area
            # check if bottom field is occupied then go left or right and check if it is on the board
            return 'down'

    def move_toward_piece(self):
        # current position
        field = self.game_info.task_fields(self.location[0], self.location[1])

        # put up piece and change self.has_piece
        if field.has_piece():
            self.has_piece = 1
            return "pickup_message"

        # move to the closest piece
        # TODO: look for closest and move toward it

        pass
