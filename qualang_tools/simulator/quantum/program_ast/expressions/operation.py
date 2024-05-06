from .expression import Expression


class Operation(Expression):
    def __init__(self, left: Expression, right: Expression, operation: str):
        self.left = left
        self.right = right
        self.operation = operation

    def __str__(self):
        return f"{self.left} {self.operation} {self.right}"