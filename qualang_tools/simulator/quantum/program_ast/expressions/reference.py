from .expression import Expression


class Reference(Expression):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name
