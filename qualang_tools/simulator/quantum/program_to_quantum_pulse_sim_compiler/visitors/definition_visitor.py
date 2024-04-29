from qualang_tools.simulator.quantum.program_ast.expressions.definition import Definition


default_values = {
    'INT': 0,
    'REAL': 0.,
    'BOOL': False,
}


class DefinitionVisitor:
    def visit(self, definition: Definition) -> dict:
        value = definition.value
        if value == []:
            if definition.type not in default_values:
                raise KeyError(f"Unrecognised variable type in definition {definition.type}")
            value = default_values[definition.type]

        return {definition.name: value}
