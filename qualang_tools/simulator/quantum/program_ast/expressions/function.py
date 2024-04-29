from typing import List

from .expression import Expression


class Function(Expression):
    def __init__(self, arguments: List[Expression], function_name: str, library_name: str):
        self.arguments = arguments
        self.function_name = function_name
        self.library_name = library_name
