class CustomBaseExceptionWithMessage(BaseException):
    # extend BaseException class and add functionality that is passing a string which will describe the error
    # the error message will also be produced when printing this exception to sout
    def __init__(self, message=None):
        super(CustomBaseExceptionWithMessage, self).__init__()
        if message is not None:
            self.error_message = message
        else:
            self.error_message = None

    def __str__(self):
        if self.error_message is not None:
            return self.error_message
        else:
            return "Unspecified error message."


class GameConnectionError(CustomBaseExceptionWithMessage):
    # should be used whenever something wrong happens with connection itself (fail to connect etc.)
    pass


class UnexpectedServerMessage(CustomBaseExceptionWithMessage):
    # we received a message from the server which we didn't expect
    pass


class UnexpectedClientMessage(CustomBaseExceptionWithMessage):
    # server received an unexpected message from client
    pass


class StrategicError(CustomBaseExceptionWithMessage):
    # something wrong in strategy...
    pass


class LocationOutOfBoundsError(CustomBaseExceptionWithMessage):
    def __init__(self, location, message=""):
        super(LocationOutOfBoundsError, self).__init__(
            message + "The provided location: " + str(location) + " was out of bounds.")
