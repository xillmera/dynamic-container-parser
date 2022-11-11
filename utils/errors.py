# serialization.db.tables (target)
class InsertionFailure(BaseException):
    pass


class NoUniqueID(BaseException):
    pass


class NoFurtherRequired(BaseException):
    pass


# .abstractElementExtractor
class UnrecognizableURLPage (Exception):
    def __init__(self):
        pass


class FieldNotAvailable(ValueError):
    # Constructor method
    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        tmp = f'Unable to allocate {self.description}'
        return tmp


class BadRequest(BaseException):
    pass


class WrongConfiguration(BaseException):
    pass

class StrategyFailure(BaseException):
    pass


class StrategyNotDetected(BaseException):
    pass

