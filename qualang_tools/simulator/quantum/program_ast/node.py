class Node:
    def accept(self, visitor, context):
        visitor.visit(self, context)
