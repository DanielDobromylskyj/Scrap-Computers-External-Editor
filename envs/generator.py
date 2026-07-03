import json
import re

def create_definition_file(lua_path, output_path):
    definition_data = {}

    with open(lua_path, "r", encoding="utf8") as f:
        lines = f.read().split("\n")

    current_class_definition = {
        "name": "",
        "fields": {},
        "alias": ""
    }

    current_func_definition = {
        "name": "",
        "params": [],
        "returns": []
    }

    for line in lines:
        if (len(line) > 4 and line.startswith("---") and line[3] not in ("-", " ")) or line.startswith("func"):
            if line.startswith("---@class"):
                name = f"!{line.split(' ')[1]}"
                current_class_definition["name"] = name
                assert isinstance(name, str), "PyCharm was actually correct for once!"

                definition_data[name] = current_class_definition

                current_class_definition = {
                    "name": "",
                    "fields": {},
                    "alias": ""
                }

            elif line.startswith("---@field"):
                chunks = line.split(" ")
                assert isinstance(current_class_definition["fields"], dict), "PyCharm was actually correct for once!"

                current_class_definition["fields"][chunks[1]] = {
                    "type": chunks[2],
                    "desc": " ".join(chunks[3:])
                }


            elif line.startswith("---@alias"):
                chunks = line.split(" ")
                current_class_definition["alias"] = chunks[1]

            elif line.startswith("---@return") or line.startswith("---@reutrn"):  # W coding
                returns = current_func_definition["returns"]
                assert isinstance(returns, list), "PyCharm was actually correct for once!"
                returns.append(line.split(" ")[1])

            elif line.startswith("---@param"):
                params = current_func_definition["params"]
                assert isinstance(params, list), "PyCharm was actually correct for once!"
                params.append(line.split(" ")[1])
                current_func_definition["params"] = params

            elif line.startswith("function"):
                chunks = line.split(" ")
                name = chunks[1].split("(")[0]
                current_func_definition["name"] = name
                assert isinstance(name, str), "PyCharm was actually correct for once!"

                definition_data[name] = current_func_definition

                current_func_definition = {
                    "name": "",
                    "params": [],
                    "returns": []
                }



    splits = [":", "."]
    name_splitter = "(" + "|".join(map(re.escape, splits)) + ")"

    output_json = {}
    for name, data in definition_data.items():
        name_stack = re.split(name_splitter, name)

        location = output_json
        for segment in name_stack:
            if segment in splits:
                continue

            if segment not in location:
                location[segment] = {"content": {}, "type": "struct"}



            location = location[segment]["content"]

        if "params" in data:  # Function
            location["type"] = "function"
            location["content"] = {
                "name": data["name"],
                "params": data["params"],
                "returns": data["returns"]
            }

        if "fields" in data:
            location["type"] = "class"
            location["content"] = {
                "name": data["name"],
                "fields": data["fields"],
                "alias": data["alias"]
            }



    with open(output_path, "w", encoding="utf8") as f:
        json.dump({"content": output_json, "type": "struct"}, f, indent=4, ensure_ascii=False)

