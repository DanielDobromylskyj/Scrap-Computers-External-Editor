import os

def convert_hex_to_rgb(hex_colour) -> tuple[int, int, int]:
    hex_colour = hex_colour.strip("#")

    if len(hex_colour) != 6:
        raise ValueError("Hex colour must be 6 characters long")

    try:
        r = int(hex_colour[0:2], 16)
        g = int(hex_colour[2:4], 16)
        b = int(hex_colour[4:6], 16)
    except ValueError:
        raise ValueError("Invalid hex colour")

    return r, g, b


def validate(data):
    if "HEADER" not in data:
        raise SyntaxError("Missing 'HEADER' section in theme file")

    if "LANGUAGE" not in data["HEADER"]:
        raise SyntaxError("Missing 'LANGUAGE' value in 'HEADER' section in theme file")

    if "COLOURS" not in data:
        raise SyntaxError("Missing 'COLOURS' section in theme file")

    if "KEYWORDS" not in data:
        raise SyntaxError("Missing 'KEYWORDS' section in theme file")

def parse_colours(data):
    def parse_func(func: str) -> str:
        return func.split("(")[1].split(")")[0]

    def parse_rgb(raw: str) -> tuple[int, int, int]:
        chunks = raw.replace(" ", "").split(",")
        assert len(chunks) == 3, "Invalid RGB Syntax"
        return int(chunks[0]), int(chunks[1]), int(chunks[2])

    output = {}

    for key, value in data.items():
        if value.startswith("rgb"):
            colour = parse_rgb(parse_func(value))
        elif value.startswith("hex"):
            colour = convert_hex_to_rgb(parse_func(value))
        else:
            raise SyntaxError(f"Invalid colour value: '{value}'")

        output[key] = colour

    return output

class Theme:
    def __init__(self, path):
        self.path = path

        if not os.path.exists(path):
            raise FileNotFoundError(path)

        data = self.__parse()
        validate(data)

        self.colours: dict = parse_colours(data["COLOURS"])
        self.keywords: dict = data["KEYWORDS"]
        self.target_language: str = data["HEADER"]["LANGUAGE"]

    def __parse(self):
        with open(self.path, "r") as f:
            lines = f.read().split("\n")

        parsed = {}

        current_header = None
        for line in lines:
            if line.strip() == "":
                continue

            if line.startswith(" "):
                if not current_header:
                    raise SyntaxError(f"Attempted to set a value before giving a section header")

                assert current_header in parsed

                if "=" in line:
                    key, value = line.strip().split("=")

                else:
                    value = line.strip(" ")
                    key = len(parsed[current_header])

                if key in parsed[current_header]:
                    print("[WARNING] Duplicate key found while parsing theme")

                parsed[current_header][key] = value

            elif line.startswith("#"):
                pass   # Comment

            elif line.endswith(":"):
                current_header = line[:-1]

                if current_header not in parsed:
                    parsed[current_header] = {}

            else:
                raise SyntaxError(f"Invalid syntax on line '{line}'")

        return parsed

    def set_theme(self, syntax_highlighter):
        if syntax_highlighter.LANGUAGE != self.target_language:
            raise TypeError(f"Theme/Highlighter Language Mismatch! ({syntax_highlighter.LANGUAGE} vs {self.target_language})")

        for key, colour in self.colours.items():
            attr_name = f"{key.upper()}_COLOUR"

            if hasattr(syntax_highlighter, attr_name):
                setattr(syntax_highlighter, attr_name, colour)

            else:
                print(f"[WARNING] Unknown theme colour key '{key}'")

        syntax_highlighter.KEYWORDS = {
            keyword: syntax_highlighter.KEYWORD_COLOUR
            for keyword in self.keywords.values()
        }
