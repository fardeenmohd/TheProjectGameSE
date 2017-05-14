class UnexpectedServerMessage(BaseException):
    # we received a message from the server which we didn't expect
    pass


class UnexpectedClientMessage(BaseException):
    # server received an unexpected message from client
    pass


class StrategicError(BaseException):
    # something wrong in strategy...
    pass


class BoardError(BaseException):
    # very general error which should be thrown when an invalid operation is attempted on the board
    def __init__(self, message=None):
        super(BoardError, self).__init__()
        if message is not None:
            self.error_message = message
        else:
            self.error_message = None

    def __str__(self):
        if self.error_message is not None:
            return "BoardError: " + self.error_message
        else:
            return "Unspecified BoardError."


class LocationOutOfBoundsError(BoardError):
    def __init__(self, location, message=""):
        super(LocationOutOfBoundsError, self).__init__(
            message + "The provided location: " + str(location) + " was out of bounds.")
