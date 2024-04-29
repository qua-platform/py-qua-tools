import numbers

from .expression import Expression


class Literal(Expression):
    def __init__(self, value: numbers.Number):
        self.value = value