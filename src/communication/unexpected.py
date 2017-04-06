class UnexpectedServerMessage(BaseException):
    # we received a message from the server which we didn't expect
    pass


class UnexpectedClientMessage(BaseException):
    # server received an unexpected message from client
    pass
