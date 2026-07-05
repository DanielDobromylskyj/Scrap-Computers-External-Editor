import re
import time


class OpenFile:
    def __init__(self, syntax_highlighter, fileObj):
        self.syntaxHighlighter = syntax_highlighter
        self.obj = fileObj

        self.__raw = None
        self.raw_lines = []
        self.onLoad_chunks = []
        self.lines = []

    @staticmethod
    def convert_code_chunks_to_lines(chunks):
        lines = []
        active_line = []
        for chunk1, colour in chunks:
            for chunk2 in re.split(r'(\r?\n)', chunk1):
                if chunk2 == "\n":
                    lines.append(active_line)
                    active_line = []

                else:
                    active_line.append((chunk2, colour))

        lines.append(active_line)
        return lines

    def newline(self, line_index):
        self.lines.insert(line_index, [])
        self.raw_lines.insert(line_index, "")

    def remove_line(self, line_index):
        self.lines.pop(line_index)
        self.raw_lines.pop(line_index)

    def syntax_area(self, start_index, end_index):
        code = "\n".join(self.raw_lines[start_index:end_index])

        chunks = self.syntaxHighlighter.highlight(code)
        lines = self.convert_code_chunks_to_lines(chunks)

        for dy in range(end_index - start_index):
            line_index = start_index + dy

            if self.lines[line_index] != lines[dy]:
                self.lines[line_index] = lines[dy]
                self.raw_lines[line_index] = "".join(text for text, _ in lines[dy])

    def validate(self):
        assert len(self.raw_lines) == len(self.lines), "Validation Failed: Raw/Highlighted line counts desynced"

        for i in range(len(self.raw_lines)):
            expected = "".join(text for text, _ in self.lines[i])
            assert self.raw_lines[i] == expected, f"Validation Failed: Raw/Highlighted line {i+1} mis-match"

    def open(self):
        dat = self.obj.read()

        if dat is None:
            print("[WARNING] Computer failed to load obj. Retrying")
            dat = self.obj.read()

            if dat is None:
                print("[WARNING] Failed to open file")
                return

        self.__raw = dat.replace("\t", "    ")

        start = time.time()
        while (not self.__raw) and (start + 1 > time.time()):
            self.__raw = self.obj.read()

        if self.__raw is None:
            self.__raw = ""
            print("[WARNING] Failed to load file")

        self.raw_lines = self.__raw.split("\n")
        self.onLoad_chunks = self.syntaxHighlighter.highlight(self.__raw)
        self.lines = [None] * len(self.raw_lines)
        self.syntax_area(0, len(self.raw_lines))
        self.validate()

    def save(self):
        content = "\n".join([
            "".join(chunk for chunk, colour in line)
            for line in self.lines
        ])
        self.obj.write(content)

        self.validate()