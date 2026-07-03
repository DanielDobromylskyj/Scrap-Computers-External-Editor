import copy
import json
import re

import tree_sitter_lua as ts_lua
from tree_sitter import Language, Parser, Node

LUA_LANGUAGE = Language(ts_lua.language())


class DefinitionMap:
    TYPE_NOT_SET = "unset"
    TYPE_TABLE = "table"
    TYPE_VARIABLE = "variable"
    TYPE_FUNCTION = "function"

    def __init__(self):
        self.variables: dict = {}

    def populate_to_stack(self, src, stack: list[str]) -> dict:
        """ Fills in the definitions dict so that the stack is always valid, then returns the top level of the stack """
        current = self.variables
        for step in stack:
            if step not in current:
                current[step] = {"src":src, "content": {}, "type": self.TYPE_TABLE}

            current = current[step]["content"]
        return current


    def create_function(self, src, stack: list[str], name: str, returns: list, params: list[str]):
        scope = self.populate_to_stack(src, stack)
        scope[name] = {"params": params, "returns": returns, "src": src, "type": self.TYPE_FUNCTION}

    def create_variable(self, src,  stack: list[str], name: str, likely_type: list):
        scope = self.populate_to_stack(src, stack)
        scope[name] = {"src": src, "type": self.TYPE_VARIABLE, "var_type": likely_type[-1] if len(likely_type) > 0 else None}

    def __search(self, stack: list[str], find_exact=False):
        current = self.variables
        found = []
        for i, step in enumerate(stack):
            if i == len(stack) - 1:
                for key in current.keys():

                    if key == step and not find_exact:
                        continue

                    if key == "content" and type(current["content"]) is dict:
                        continue

                    if key == "type" and type(current["type"]) is str:
                        continue

                    if key.lower().startswith(step.lower()) and not find_exact:
                        found.append(key)

                    if find_exact and key == step:
                        found.append(current[key])

            if step not in current:
                return found

            if current[step]["type"] == self.TYPE_TABLE:
                current = current[step]["content"]

            elif current[step]["type"] == self.TYPE_VARIABLE:
                var = current[step]

                if "var_type" in var and var["var_type"] is not None:
                    var_type = var["var_type"]

                    stack2 = [var_type, *stack[i+1:]]
                    return self.__search(stack2)


            else:
                break

        return found


    def search(self, stack: list[str], query: list[str], find_exact=False):
        stack.extend(query)

        found = self.__search(stack, find_exact)
        found.extend(self.__search(query, find_exact))

        return found

    def __str__(self):
        return f"Scope: {self.variables}"


class Globals:
    def __init__(self, path):
        self.path = path
        self.data = json.loads(open(path).read())

    def __recursive_add_funcs(self, definition_map, stack: list[str], data):
        if data["type"] == "struct":
            content = data["content"]
            if isinstance(content, dict) and "type" in content and isinstance(content["type"], str):
                self.__recursive_add_funcs(definition_map, stack, data["content"])
            else:
                for section_name, value in content.items():
                    sub_stack = copy.deepcopy(stack)
                    sub_stack.append(section_name)

                    self.__recursive_add_funcs(definition_map, sub_stack, value)

        elif data["type"] == "function":
            content = data["content"]
            name = stack.pop(-1)

            definition_map.create_function(None, stack, name, content["returns"], content["params"])

    def add_to_map(self, definition_map):
        self.__recursive_add_funcs(definition_map, [], self.data)


class Source:
    def __init__(self, lua, path):
        self.path = path
        self.text = lua

        self.map = DefinitionMap()  # Will be over-written later, just a placeholder

        self.parser = Parser(LUA_LANGUAGE)
        self.tree = self.parser.parse(bytes(self.text, "utf8"))

        self.exceptions: list[list[dict] | None] = [None] * (self.text.count("\n") + 1)

    def throw_exception(self, node: Node, exception: str | None = None):
        if self.exceptions[node.start_point.row] is None:
            self.exceptions[node.start_point.row] = []

        self.exceptions[node.start_point.row].append({
            "start": node.start_point,
            "end": node.end_point,
            "text": node.text,
            "exception": node.text if not exception else exception
        })


    def search_for_return_type(self, stack: list[str]) -> list[str]:
        a, b = stack[:-1], [stack[-1]]
        result = self.map.search(a, b, find_exact=True)

        if len(result) == 0:
            return []

        return result[0]["returns"]


    def get_likely_type(self, node: Node) -> list:
        data = []
        for sub_node in node.children:
            if sub_node.type == "bracket_index_expression":
                data.extend(
                    self.get_likely_type(sub_node)
                )

            elif sub_node.type == "function_call":
                data.extend(
                    self.get_likely_type(sub_node)
                )

            elif sub_node.type == "dot_index_expression":
                chunks = re.split(r"[:.]", sub_node.text.decode("utf8"))
                return_type = self.search_for_return_type(chunks)
                data.extend(return_type)

            elif sub_node.type == "[":  # Index! We don't care what, it's just an index
                if len(data) == 0:
                    return []  # IDK man wtf, go syntax error yourself or something, I suck at lua

                if data[-1].endswith("[]"):
                    name = data.pop(-1)
                    data.append(name[:-2])

        return data

    def analyze_variable_declaration(self, node: Node, stack: list[str]):
        assert node.type == "variable_declaration"

        is_local = False
        variable_names = []
        likely_type = []

        for child in node.children:
            if child.type == "assignment_statement":
                for sub_node in child.children:
                    if sub_node.type == "variable_list":
                        for identifier_node in sub_node.children:
                            if identifier_node.type == "identifier":
                                variable_names.append(identifier_node.text.decode("utf8"))

                    elif sub_node.type == "expression_list":
                        likely_type = self.get_likely_type(sub_node)

            elif child.type == "local":
                is_local = True


        for variable_name in variable_names:
            if is_local:
                self.map.create_variable(self, stack, variable_name, likely_type)
            else:
                self.map.create_variable(self, [], variable_name, likely_type)

    def analyze_function_declaration(self, node: Node, stack: list[str]):
        stack: list[str] = copy.deepcopy(stack)
        identifier = None
        is_local = False
        used_dot_index = False
        params = []
        local_stack = []

        for child in node.children:
            if child.type == "ERROR":
                self.throw_exception(child)

            elif child.type == "identifier":
                identifier = child.text.decode("utf8")
                used_dot_index = False

            elif child.type in ("dot_index_expression", "method_index_expression"):
                for sub_node in child.children:
                    if sub_node.type == "identifier":
                        if identifier is not None:
                            local_stack.append(identifier)

                        identifier = sub_node.text.decode("utf8")
                        used_dot_index = child.type == "dot_index_expression"

            elif child.type == "local":
                is_local = True

            elif child.type == "parameters":
                for parameter_node in child.children:
                    if parameter_node.type == "identifier":
                        params.append(parameter_node.text.decode("utf8"))

            elif child.type == "function":
                pass # todo - parse sub data  - Its been 3 days, this shit aint happening

        assert identifier is not None

        if used_dot_index:
            params.append("self")


        if is_local:
            stack.extend(local_stack)
            self.map.create_function(self, stack, identifier, params, [])
        else:
            self.map.create_function(self, local_stack, identifier, params, [])

    def error_scan(self, node: Node):
        if node.is_error:
            self.throw_exception(node)

        else:
            for child in node.children:
                if child.has_error:
                    self.error_scan(child)

    def __analyze(self, node, stack: list[str]):
        for child in node.children:
            if child.has_error:
                self.error_scan(child)

            if child.type == "variable_declaration":
                self.analyze_variable_declaration(child, stack)

            elif child.type == "function_declaration":
                self.analyze_function_declaration(child, stack)

    def scan_and_delete(self, definitions: dict, is_function: bool):
        keys = list(definitions.keys())

        for definition in keys:
            data = definitions[definition]

            if is_function:
                if "src" in data:
                    if data["src"] == self:
                        definitions.pop(definition)

                else:
                    self.scan_and_delete(data, is_function)
                    definitions.pop(definition)

            else:
                if type(data) is dict and "src" in data:
                    if data["src"] == self:
                        definitions.pop(definition)

                elif data == self:
                    definitions.pop(definition)

                else:
                    self.scan_and_delete(data, is_function)
                    definitions.pop(definition)

    def reanalyze(self, text, stack: list[str]):
        self.scan_and_delete(self.map.variables, is_function=False)

        self.text = text
        self.tree = self.parser.parse(bytes(self.text, "utf8"))

        self.analyze(self.map, stack)


    def analyze(self, definition_map, stack: list[str]):
        self.exceptions: list[list[dict] | None] = [None] * (self.text.count("\n") + 1)

        self.map = definition_map
        self.__analyze(self.tree.root_node, stack)


class Analyzer:
    def __init__(self, globals_data: None | list[Globals]=None):
        self.map = DefinitionMap()
        self.sources: list[Source] = []

        if globals_data is not None:
            for global_data in globals_data:
                global_data.add_to_map(self.map)

    def reanalyze_source(self, src_id: int, text: str):
        src = self.sources[src_id]
        src.reanalyze(text, [src.path])

    def add_source(self, source: Source) -> int:
        source.analyze(self.map, [source.path])
        self.sources.append(source)

        return len(self.sources) - 1

    def get_source(self, src_id):
        return self.sources[src_id]
