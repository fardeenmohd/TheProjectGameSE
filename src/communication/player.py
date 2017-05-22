#!/usr/bin/env python
import xml.etree.ElementTree as ET
from argparse import ArgumentParser

from src.communication import messages
from src.communication.client import Client
from src.communication.info import GameInfo, PlayerType, Allegiance, PieceInfo, ClientTypeTag, PlayerInfo
from src.communication.strategy import StrategyFactory, Decision
from src.communication.unexpected import UnexpectedServerMessage

REGISTERED_GAMES_TAG = "{https://se2.mini.pw.edu.pl/17-results/}"


def parse_games(games):
    open_games = []
    root = ET.fromstring(games)

    for registered_games in root.findall(REGISTERED_GAMES_TAG + "GameInfo"):
        game_name = registered_games.get("gameName")
        blue_team_players = int(registered_games.get("blueTeamPlayers"))
        red_team_players = int(registered_games.get("redTeamPlayers"))
        open_games.append((game_name, blue_team_players, red_team_players))

    return open_games


class Player(Client):
    def __init__(self, index=0, verbose=False, game_name='easy clone'):
        """

        :param index: Player index for the server
        :param verbose: Verbose functionality boolean
        :param game_name: Game name for player to join
        """
        super().__init__(index, verbose)

        self.typeTag = ClientTypeTag.PLAYER
        self.Guid = 'Not Assigned'
        self.game_info = GameInfo()
        self.open_games = []
        self.game_name = game_name
        self.team = 'Not Assigned'
        self.type = 'Not Assigned'
        self.location = tuple()
        self.game_on = False

        self.strategy = None

    def handle_confirmation(self, message: str):
        """
        Parses the confirmation message and extracts game information
        """
        if "ConfirmJoiningGame" in message:
            root = ET.fromstring(message)
            self.Guid = root.attrib.get('privateGuid')
            self.game_info.id = str(root.attrib.get('gameId'))
            self.game_info.name = self.game_name
            self.id = root.attrib.get('playerId')

            for player_definition in root.findall(REGISTERED_GAMES_TAG + "PlayerDefinition"):
                self.team = player_definition.attrib.get('team')
                self.type = player_definition.attrib.get('type')

            self.verbose_debug("Got assigned role of " + self.type + " in team " + self.team)

            return True

        elif "RejectJoiningGame" in message:
            self.verbose_debug("Got rejected by the server, so shutting down.")
            self.shutdown()
            return False

        else:
            raise UnexpectedServerMessage("Unexpected message from server!")

    def handle_game(self, game_message: str):
        """
        Parses a Game message, sets up self.game_info
        """
        root = ET.fromstring(game_message)

        for board in root.findall(REGISTERED_GAMES_TAG + "Board"):
            self.game_info.task_height = int(board.attrib.get('tasksHeight'))
            self.game_info.board_width = int(board.attrib.get('width'))
            self.game_info.goals_height = int(board.attrib.get('goalsHeight'))

        for player_location in root.findall(REGISTERED_GAMES_TAG + "PlayerLocation"):
            x = int(player_location.attrib.get('x'))
            y = int(player_location.attrib.get('y'))
            self.location = (x, y)

        for player_list in root.findall(REGISTERED_GAMES_TAG + "Players"):
            for in_player in player_list.findall(REGISTERED_GAMES_TAG + "Player"):
                in_team = in_player.attrib.get('team')
                in_type = in_player.attrib.get('type')
                in_id = in_player.attrib.get('id')
                self.game_info.teams[in_team][in_id] = PlayerInfo(in_id, in_type, in_type)

        self.game_info.initialize_fields()

    def handle_data(self, response_data: str):
        """
        parses a Data messsage, updates self.game_info
        """
        root = ET.fromstring(response_data)

        if root.attrib.get('gameFinished') == 'true':
            self.game_on = False

        for task_field_list in root.findall(REGISTERED_GAMES_TAG + "TaskFields"):
            if task_field_list is not None:
                for task_field in task_field_list.findall(REGISTERED_GAMES_TAG + "TaskField"):
                    x = int(task_field.attrib.get('x'))
                    y = int(task_field.attrib.get('y'))
                    self.game_info.task_fields[x, y].timestamp = task_field.attrib.get('timestamp')
                    self.game_info.task_fields[x, y].distance_to_piece = int(task_field.attrib.get('distanceToPiece'))
                    if task_field.attrib.get('playerId') is not None:
                        self.game_info.task_fields[x, y].player_id = str(task_field.attrib.get('playerId'))
                    else:
                        self.game_info.task_fields[x, y].player_id = "-1"
                    if task_field.attrib.get('pieceId') is not None:
                        self.game_info.task_fields[x, y].piece_id = str(task_field.attrib.get('pieceId'))
                    else:
                        self.game_info.task_fields[x, y].piece_id = "-1"

        for goal_field_list in root.findall(REGISTERED_GAMES_TAG + "GoalFields"):
            if goal_field_list is not None:
                for goal_field in goal_field_list.findall(REGISTERED_GAMES_TAG + "GoalField"):
                    x = int(goal_field.attrib.get('x'))
                    y = int(goal_field.attrib.get('y'))
                    self.game_info.goal_fields[x, y].timestamp = goal_field.attrib.get('timestamp')
                    if goal_field.attrib.get('playerId') is not None:
                        self.game_info.goal_fields[x, y].player_id = str(goal_field.attrib.get('playerId'))
                    self.game_info.goal_fields[x, y].allegiance = goal_field.attrib.get('team')
                    self.game_info.goal_fields[x, y].type = goal_field.attrib.get('type')

        for piece_list in root.findall(REGISTERED_GAMES_TAG + "Pieces"):
            if piece_list is not None:
                for piece in piece_list.findall(REGISTERED_GAMES_TAG + "Piece"):
                    id = piece.attrib.get('id')
                    timestamp = piece.attrib.get('timestamp')
                    type = piece.attrib.get('type')
                    player_id = piece.attrib.get('playerId')
                    if player_id is not None:
                        self.game_info.pieces[id] = PieceInfo(id, type, player_id, timestamp=timestamp)
                    else:
                        self.game_info.pieces[id] = PieceInfo(id, type, timestamp=timestamp)

        for player_location in root.findall(REGISTERED_GAMES_TAG + "PlayerLocation"):
            if player_location is not None:
                x = int(player_location.attrib.get('x'))
                y = int(player_location.attrib.get('y'))
                self.location = (x, y)

    def receive(self):
        """
        overriding the parent method to implement re-joining when GM disconnects
        """
        received = super(Player, self).receive()
        if "GameMasterDisconnected" in received:
            # clean up our knowledge and try to join to the game again.
            self.game_on = False
            self.verbose_debug("GameMaster has disconnected! Trying to join game again...")
            if not self.try_join():
                # if we failed to join, kys
                self.verbose_debug("Failed to re-join game. Shutting down.")
                self.shutdown()
        return received

    def try_join(self):
        self.send(messages.GetGames())
        games = self.receive()

        if 'RegisteredGames' in games:
            self.open_games = parse_games(games)

            if len(self.open_games) > 0:
                temp_game_name = self.game_name
                temp_preferred_role = PlayerType.LEADER.value
                temp_preferred_team = Allegiance.RED.value
                self.send(messages.JoinGame(temp_game_name, temp_preferred_team, temp_preferred_role))

                confirmation = self.receive()
                if confirmation is not None:
                    self.handle_confirmation(confirmation)
                else:
                    raise UnexpectedServerMessage("Game registering confirmation was None!")

                game_message = self.receive()
                if game_message is not None:
                    self.handle_game(game_message)
                    return True
                else:
                    raise UnexpectedServerMessage("Game message was None!")
        return False

    def play(self):
        self.game_on = True
        self.strategy = StrategyFactory(self.team, self.location, self.game_info)

        while self.game_on:
            # find the next decision, send a message specified by it.
            decision = self.strategy.get_next_move(self.location)

            self.send(self.choose_message(decision))

            response = self.receive()
            if response is None:
                self.verbose_debug("Something wrong happened to the server! Shutting down.")
                self.shutdown()

            else:
                # normal response!
                self.handle_data(response)
                # if we just succesfully moved, we need to update our info
                # specifically, update player_id on the field we just left (make it empty again)
                # for this I'm using strategy.current_location which hasn't been updated yet and so is the prev. loc.
                old_location = self.strategy.current_location
                if self.strategy.last_move.choice == Decision.MOVE and self.location != old_location:
                    if self.game_info.is_task_field(old_location):
                        self.game_info.task_fields[old_location].player_id = "-1"
                    else:
                        self.game_info.goal_fields[old_location].player_id = "-1"

                if self.strategy.last_move.choice == Decision.PICK_UP:
                    # check if we have a piece now
                    for piece_info in self.game_info.pieces.values():
                        if piece_info.player_id == self.id:
                            self.strategy.have_piece = piece_info.id
                            self.game_info.task_fields[old_location].piece_id = "-1"
                            self.game_info.update_field_distances()
                            break
                    else:
                        self.strategy.have_piece = "-1"

                self.strategy.current_location = self.location

        self.shutdown()

    def choose_message(self, decision: Decision) -> str:
        """
        :returns: an appropriate message string basing on decision.
        """
        if decision.choice == Decision.DISCOVER:
            return messages.Discover(self.game_info.id, self.Guid)

        elif decision.choice == Decision.MOVE:
            direction = decision.additional_info
            if direction is None:
                  return messages.Discover(self.game_info.id, self.Guid)

            return messages.Move(self.game_info.id, self.Guid, direction)

        elif decision.choice == Decision.PICK_UP:
            return messages.PickUpPiece(self.game_info.id, self.Guid)

        elif decision.choice == Decision.PLACE:
            return messages.PlacePiece(self.game_info.id, self.Guid)


if __name__ == '__main__':
    def simulate(player_count, verbose, game_name):
        for i in range(player_count):
            p = Player(index=i, verbose=verbose, game_name=game_name)
            if p.connect():
                if p.try_join():
                    p.play()
                    p.shutdown()


    parser = ArgumentParser()
    parser.add_argument('-c', '--playercount', default=1, help='Number of players to be deployed.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Use verbose debugging mode.')
    parser.add_argument('-n', '--gamename', default="easy clone", help="Name of the game", type=str)
    args = vars(parser.parse_args())
    simulate(int(args["playercount"]), args["verbose"], str(args["gamename"]))
