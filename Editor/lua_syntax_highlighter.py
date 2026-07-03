import re

separators = ["--", "==", "'", '"',  *list("+-/*=~., [{()}]:"), "\n"]
pattern = "(" + "|".join(map(re.escape, separators)) + ")"


class SyntaxHighlighter:
    LANGUAGE = "lua 5.1"
    DEFAULT_COLOUR = (0,0,0)
    KEYWORD_COLOUR = (0,0,0)
    COMMENT_COLOUR = (0,0,0)
    STRING_COLOUR = (0,0,0)
    NUMERIC_COLOUR = (0,0,0)
    FUNCTION_NAME_COLOUR = (0,0,0)
    FUNCTION_CALL_COLOUR = (0,0,0)
    PARAM_COLOUR = (0,0,0)

    KEYWORDS = {}

    def highlight(self, text):
        segments = re.split(pattern, text)

        output = []

        in_comment = False
        in_string = False
        string_type = None

        last_segment = None
        last2_segment = None
        last_keyword = None

        for i, segment in enumerate(segments):
            next_segment = segments[i+1] if i+1 < len(segments) else None
            colour = self.DEFAULT_COLOUR

            if segment.isnumeric():
                colour = self.NUMERIC_COLOUR

            if segment in self.KEYWORDS:
                colour = self.KEYWORDS[segment]
                last_keyword = segment


            if last_keyword == "function" and segment not in list("(), ") and segment != "function":
                colour = self.PARAM_COLOUR

            if last2_segment == "function" and last_segment == " ":
                colour = self.FUNCTION_NAME_COLOUR

            if last_segment == ":":
                colour = self.FUNCTION_CALL_COLOUR

            if next_segment == "(" and last2_segment != "function":
                colour = self.FUNCTION_CALL_COLOUR

            # Comment Colour Control
            if segment == "--" and not in_string:
                in_comment = True

            if in_comment and (segment == "\n" or segment == "\r\n"):
                in_comment = False

            if in_comment:
                colour = self.COMMENT_COLOUR




            if in_string and segment == string_type:
                colour = self.STRING_COLOUR
                in_string = False
                string_type = None

            elif (segment == "'" or segment == '"') and not in_comment:
                in_string = True
                string_type = segment

            if in_string:
                colour = self.STRING_COLOUR

            # No more colouring
            last2_segment = last_segment
            last_segment = segment

            # See if we need to combine or create new
            if len(output) == 0:
                output.append((segment, colour))
            else:
                last = output[-1]

                if last[1] == colour:
                    output[-1] = (last[0] + segment, last[1])

                else:
                    output.append((segment, colour))


        return output
