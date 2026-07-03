import pygame
import string
import math
import re

from .context_analyser import Analyzer, Source, Globals
from .lua_syntax_highlighter import pattern as LUA_PATTERN
from .lua_syntax_highlighter import SyntaxHighlighter as LuaSyntaxHighlighter
from .text_highlighter import SyntaxHighlighter as GeneralSyntaxHighlighter
from .OpenFile import OpenFile
from .themes import Theme


class Cursor:
    def __init__(self):
        self.x = 0
        self.y = 0

        self.char_width = 0
        self.char_height = 0

    def set_font(self, font: pygame.font.Font):
        char = font.render("#", True, (0, 0, 0))
        self.char_width, self.char_height = char.get_size()


    def limit(self, max_x, max_y):
        if max_x >= 0:
            if self.x > max_x:
                self.x = max_x

            if self.x < 0:
                self.x = 0

        if max_y >= 0:
            if self.y > max_y:
                self.y = max_y

            if self.y < 0:
                self.y = 0

class CodeEditor:
    def __init__(self, app, projectView):
        self.app = app
        self.project_view = projectView

        self.analyzer = Analyzer()
        self.path_to_source = {}

        self.lua_syntax_highlighter = LuaSyntaxHighlighter()
        Theme("themes/lua.theme").set_theme(self.lua_syntax_highlighter)

        self.general_syntax_highlighter = GeneralSyntaxHighlighter()
        Theme("themes/default.theme").set_theme(self.general_syntax_highlighter)

        self.topbar_font = pygame.font.SysFont("Monospace", 14)
        self.topbar_height = 20

        self.cursor = Cursor()

        self.line_font: pygame.font.Font | None = None
        self.line_height = None

        self.loaded_files: list[OpenFile] = []
        self.current_file_index: int | None = None

        self.lines = []
        self.lines_scrolled = 0

        self.frame_counter = 0

        self.held_keys = {}
        self.hold_time_to_repeat = 0.6

        self.possibles = []
        self.possibles_index = 0
        self.possibles_surface = None
        self.possibles_offset = 0

        # Selecting
        self.left_mouse_held = False
        self.selecting = False

        self.selection_start_x = 0
        self.selection_start_y = 0


        # Setup Init
        self.init_analyzer()
        self.move_cursor(0, 0)
        self.set_font_size(15)

    def init_analyzer(self):
        self.analyzer = Analyzer([Globals("envs/lua_sc.json"), Globals("envs/lua.json")])  # Create new analyser
        self.path_to_source = {}

        files = self.project_view.lua_files

        for i, file in enumerate(files):
            self.app.blit_text(f"Analyzing File '{file.path}' ({i+1}/{len(files)})")

            src_id = self.analyzer.add_source(Source(file.read(), file.path))
            self.path_to_source[file.path] = src_id

    def line_has_errors(self, line_index) -> list:
        assert self.current_file_index is not None, "Attempted to perform a check with no active file"
        fileObj = self.loaded_files[self.current_file_index]

        if fileObj.obj.path not in self.path_to_source:
            return []

        source_id = self.path_to_source[fileObj.obj.path]
        source = self.analyzer.get_source(source_id)

        errors = source.exceptions[line_index]
        return errors if errors is not None else []

    def set_font_size(self, font_size: int):
        self.line_font: pygame.font.Font = pygame.font.SysFont("Monospace", font_size)
        self.line_height = font_size+2

        assert self.line_font is not None
        self.cursor.set_font(self.line_font)

    def add_file(self, fileObj):
        highlighter = self.lua_syntax_highlighter if fileObj.path.endswith(".lua") else self.general_syntax_highlighter

        self.loaded_files.append(
            OpenFile(highlighter, fileObj)
        )

        self.open_file(len(self.loaded_files) - 1)

    def is_file_open(self, path: str) -> int | None:
        for file_index, file in enumerate(self.loaded_files):
            if file.obj.path == path:
                return file_index

        return None


    def open_file(self, file_index: int):
        if self.current_file_index is not None:
            old_file: OpenFile = self.loaded_files[self.current_file_index]
            old_file.save()

        self.current_file_index = file_index
        file: OpenFile = self.loaded_files[file_index]
        file.open()

        self.lines = [None] * len(file.lines)
        self.move_cursor(0, 0)

    def __redraw_line(self, line_index: int, line_width: int):
        assert self.current_file_index is not None, "Attempted to draw a line with no active file"
        assert self.line_font is not None, "Attempted to draw a line with no loaded font"

        activeFile = self.loaded_files[self.current_file_index]
        surface = pygame.Surface((line_width, self.line_height), pygame.SRCALPHA)
        line_data = activeFile.lines[line_index]

        y_offset = (self.line_height - self.line_font.get_height()) / 2
        x_offset = 0

        line_length = 0
        for chunk, colour in line_data:
            rect = self.line_font.render(chunk, True, colour)
            surface.blit(rect, (x_offset, y_offset))
            x_offset += rect.get_width()
            line_length += len(chunk)

        errors = self.line_has_errors(line_index)
        for error in errors:
            start_char_x = error["start"].column
            end_char_x = error["end"].column if error["end"].row == error["start"].row else line_length-1

            x_start = start_char_x * self.cursor.char_width
            x_end   = end_char_x   * self.cursor.char_width


            points = []
            for x in range(x_start*10, x_end*10, 1):
                y_offset = math.sin(((x/10) - x_start) * 1) * 1
                points.append(((x/10), (self.cursor.char_height-2) + y_offset))

            if len(points) > 2:
                pygame.draw.lines(surface, (255, 0, 0), False, points, 1)

            else:
                pygame.draw.line(surface, (255, 0, 0), (x_start, (self.cursor.char_height-2)), (x_end, (self.cursor.char_height-2)), 1)


        self.lines[line_index] = surface

    def set_cursor(self, x, y):
        dx = x - self.cursor.x if x != -1 else 0
        dy = y - self.cursor.y if y != -1 else 0
        self.move_cursor(dx, dy)

    def move_cursor(self, dx, dy):
        if self.current_file_index is not None:
            self.cursor.x += dx
            self.cursor.y += dy

            activeFile = self.loaded_files[self.current_file_index]
            self.cursor.limit(-1, len(self.lines)-1)

            line_data = activeFile.raw_lines[self.cursor.y]
            self.cursor.limit(len(line_data), -1)


    def update_line_syntax(self, target_index):
        assert self.current_file_index is not None, "Attempted to re-syntax a line with no active file"
        active_file = self.loaded_files[self.current_file_index]

        start_index = max(0, target_index - 1)
        end_index = min(target_index + 2, len(active_file.raw_lines))

        active_file.syntax_area(start_index, end_index)

        for i in range(start_index, end_index):
            self.lines[i] = None

        src_id = self.path_to_source[active_file.obj.path]
        self.analyzer.reanalyze_source(src_id, "\n".join(active_file.raw_lines))

    def update_current_line(self, do_area=False):
        self.update_line_syntax(self.cursor.y)

        if do_area and (self.cursor.y - 1) >= 0:
            self.update_line_syntax(self.cursor.y - 1)

        if do_area and self.cursor.y + 1 < len(self.lines):
            self.update_line_syntax(self.cursor.y + 1)

    def redraw_possibles(self):
        if len(self.possibles) == 0:
            self.possibles_surface = None
            return

        max_width = (len(max(self.possibles, key=len)) * self.cursor.char_width) + 4
        max_height = len(self.possibles) * (self.cursor.char_height + 2)

        self.possibles_surface = pygame.Surface((max_width, max_height), pygame.SRCALPHA)

        pygame.draw.rect(
            self.possibles_surface,
            (30, 30, 30),
            (0, 0, max_width, max_height),
            border_radius=5
        )

        pygame.draw.rect(
            self.possibles_surface,
            (50, 50, 50),
            (0, 0, max_width, max_height),
            width=1, border_radius=5
        )

        pygame.draw.rect(
            self.possibles_surface,
            (32, 158, 193),
            (2, (self.cursor.char_height + 2) * self.possibles_index + 2, max_width - 4, self.cursor.char_height - 2),
            border_radius=4
        )

        assert self.line_font is not None, "No font"
        for i, text in enumerate(self.possibles):
            rect = self.line_font.render(text, True, (240, 240, 240))

            self.possibles_surface.blit(
                rect,
                (2, ((self.cursor.char_height + 2) * i))
            )

    def set_possibles(self, possibles):
        self.possibles = possibles

        if len(possibles) == 0:
            self.possibles_surface = None
            self.possibles_index = 0
            self.possibles_offset = 0
            return

        if self.possibles_index >= len(self.possibles):
            self.possibles_index = len(self.possibles)-1

        self.redraw_possibles()



    def update_auto_complete(self):
        if self.current_file_index is not None:
            activeFile = self.loaded_files[self.current_file_index]
            active_line = activeFile.raw_lines[self.cursor.y]
            segments = re.split(LUA_PATTERN, active_line)
            in_string = False
            string_type = None

            chunk_index, x = 0, 0
            while chunk_index < len(segments)-1:
                chunk = segments[chunk_index]

                if chunk == ("'", '"'):
                    if in_string and string_type == chunk:
                        in_string = False
                        string_type = None

                    elif not in_string:
                        in_string = True
                        string_type = chunk

                x += len(chunk)
                if x > self.cursor.x:
                    chunk_index -= 1
                    break

                chunk_index += 1

            if in_string:
                return

            path = [segments[chunk_index]]

            while True:
                seperator = segments[chunk_index-1] if chunk_index > 1 else None

                if seperator is None or seperator not in (":", "."):
                    break

                past_chunk = segments[chunk_index-2]
                path.insert(0, past_chunk)
                chunk_index -= 2

            if len(path) > 0 and len(path[0]) > 0:
                found = self.analyzer.map.search([activeFile.obj.path], path)
                self.set_possibles(found)
                self.possibles_offset = len(path[-1])
            else:
                self.set_possibles([])

        else:
            self.set_possibles([])


    def key_press(self, unicode, key, mod):
        if self.current_file_index is not None:
            activeFile = self.loaded_files[self.current_file_index]
            active_line = activeFile.raw_lines[self.cursor.y]

            if key == pygame.K_RETURN:
                current_line, next_line = active_line[:self.cursor.x], active_line[self.cursor.x:]
                activeFile.raw_lines[self.cursor.y] = current_line

                activeFile.newline(self.cursor.y+1)
                self.lines.insert(self.cursor.y+1, None)

                self.move_cursor(0, 1)
                self.set_cursor(0, -1)

                activeFile.raw_lines[self.cursor.y] = next_line

                self.update_current_line(do_area=True)

            elif key == pygame.K_BACKSPACE:
                if self.cursor.x > 0:
                    activeFile.raw_lines[self.cursor.y] = active_line[:self.cursor.x-1] + active_line[self.cursor.x:]
                    self.move_cursor(-1, 0)
                    self.update_current_line()

                elif self.cursor.y > 0: # Remove line
                    activeFile.remove_line(self.cursor.y)
                    self.lines.pop(self.cursor.y)

                    self.move_cursor(math.inf, -1)
                    activeFile.raw_lines[self.cursor.y] = activeFile.raw_lines[self.cursor.y] + active_line
                    self.update_current_line(do_area=True)

            elif key == pygame.K_DELETE:
                if self.cursor.x == len(active_line) and self.cursor.y != len(activeFile.raw_lines) - 1:
                    last_line = activeFile.raw_lines[self.cursor.y+1]

                    activeFile.remove_line(self.cursor.y+1)
                    self.lines.pop(self.cursor.y+1)

                    activeFile.raw_lines[self.cursor.y] += last_line
                    self.update_current_line(do_area=True)

                else:
                    activeFile.raw_lines[self.cursor.y] = active_line[:self.cursor.x]  + active_line[self.cursor.x+1:]
                    self.update_current_line()

            elif key == pygame.K_TAB:
                if self.possibles:
                    possible = self.possibles[self.possibles_index]
                    activeFile.raw_lines[self.cursor.y] = active_line[:self.cursor.x - self.possibles_offset] + possible +  active_line[self.cursor.x:]
                    self.move_cursor(len(possible) - self.possibles_offset, 0)
                    self.update_current_line()
                    self.set_possibles([])
                    self.redraw_possibles()
                else:
                    activeFile.raw_lines[self.cursor.y] = active_line[:self.cursor.x] + "    " + active_line[self.cursor.x:]
                    self.move_cursor(4, 0)
                    self.update_current_line()

            elif key == pygame.K_LEFT:
                self.move_cursor(-1, 0)

            elif key == pygame.K_RIGHT:
                self.move_cursor(1, 0)

            elif key == pygame.K_UP:
                if self.possibles:
                    self.possibles_index = max(0, self.possibles_index - 1)
                    self.redraw_possibles()
                else:
                    self.move_cursor(0, -1)

            elif key == pygame.K_DOWN:
                if self.possibles:
                    self.possibles_index = min(len(self.possibles) - 1, self.possibles_index + 1)
                    self.redraw_possibles()
                else:
                    self.move_cursor(0, 1)

            elif unicode in string.printable:
                activeFile.raw_lines[self.cursor.y] = active_line[:self.cursor.x] + unicode + active_line[self.cursor.x:]
                self.move_cursor(len(unicode), 0)
                self.update_current_line()

            self.update_auto_complete()


    @property
    def selected_text(self):
        if not self.selecting:
            return None

        if self.current_file_index is None:
            return None

        activeFile = self.loaded_files[self.current_file_index]

        start_y = min(self.cursor.y, self.selection_start_y)
        end_y = max(self.cursor.y, self.selection_start_y)

        lines = activeFile.raw_lines[start_y:end_y+1]

        if len(lines) == 0:
            return ""

        elif len(lines) == 1:
            start_x = min(self.cursor.x, self.selection_start_x)
            end_x = max(self.cursor.x, self.selection_start_x)
            return lines[0][start_x:end_x]

        else:
            start_line = lines.pop(0)
            end_line = lines.pop(-1)

            if self.cursor.y > self.selection_start_y:
                start_x = self.selection_start_x
                end_x = self.cursor.x
            else:
                start_x = self.cursor.x
                end_x = self.selection_start_x

            return start_line[start_x:] + "\n" + "\n".join(lines) + "\n" + end_line[:end_x]


    def on_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (1, 2):
                x, y = event.pos

                char_x = round((x-5) / self.cursor.char_width)
                char_y = y // self.cursor.char_height

                self.set_cursor(char_x, char_y)
                self.set_possibles([])

            if event.button == 1:
                if not self.left_mouse_held:
                    self.selecting = False

                self.selection_start_x = self.cursor.x
                self.selection_start_y = self.cursor.y
                self.left_mouse_held = True

        elif event.type == pygame.MOUSEWHEEL:
            if event.y < 0:
                self.possibles_index = min(len(self.possibles) - 1, self.possibles_index + 1)
                self.redraw_possibles()

            if event.y > 0:
                self.possibles_index = max(0, self.possibles_index - 1)
                self.redraw_possibles()

            self.redraw_possibles()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.left_mouse_held = False

        elif event.type == pygame.MOUSEMOTION:
            if self.left_mouse_held:
                x, y = event.pos
                char_x = round((x-5) / self.cursor.char_width)
                char_y = y // self.cursor.char_height

                if char_x != self.cursor.x or char_y != self.cursor.y:
                    self.selecting = True
                    self.set_cursor(char_x, char_y)


    def on_update(self, deltaTime: float):
        self.frame_counter += 1
        for key, [timer, data] in self.held_keys.items():
            if timer > self.hold_time_to_repeat:
                if self.frame_counter % 5 == 0:
                    self.key_press(*data)

            self.held_keys[key][0] += deltaTime


    def onkey_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.held_keys[event.key] = [0, (event.unicode, event.key, event.mod)]
            self.key_press(event.unicode, event.key, event.mod)

        if event.type == pygame.KEYUP:
            if event.key in self.held_keys:
                self.held_keys.pop(event.key)


    def draw(self, surface: pygame.Surface):
        line_width = surface.get_width() - 4

        surface.fill((0, 0, 0, 0))
        pygame.draw.rect(
            surface,
            (30, 30, 30, 255),
            (0, 0, *surface.get_size()),
            border_radius=5
        )

        if self.current_file_index is not None:
            activeFile = self.loaded_files[self.current_file_index]

            max_lines_visible = surface.get_height() // self.line_height
            end_line = min(max_lines_visible + self.lines_scrolled, len(self.lines))

            y_offset = 0
            for line_index in range(self.lines_scrolled, end_line):
                line: pygame.Surface | None = self.lines[line_index]

                if line is None or line.get_width() != line_width:
                    self.__redraw_line(line_index, line_width)
                    line: pygame.Surface = self.lines[line_index]

                surface.blit(line, (2, y_offset))
                y_offset += self.line_height


            if self.selecting:
                #print(self.selected_text)

                if self.selection_start_y == self.cursor.y:
                    min_x = min(self.selection_start_x, self.cursor.x)
                    max_x = max(self.selection_start_x, self.cursor.x)

                    x_start = min_x * self.cursor.char_width
                    x_width = (max_x - min_x) * self.cursor.char_width

                    y_start = self.line_height * self.cursor.y

                    rect_surf = pygame.Surface((x_width, self.line_height), pygame.SRCALPHA)
                    rect_surf.fill((50, 50, 200, 140))

                    surface.blit(rect_surf, (2 + x_start, y_start))

                else:
                    if self.selection_start_y > self.cursor.y:
                        min_y = self.cursor.y
                        max_y = self.selection_start_y
                        min_x = self.cursor.x
                        max_x = self.selection_start_x
                    else:
                        min_y = self.selection_start_y
                        max_y = self.cursor.y
                        min_x = self.selection_start_x
                        max_x = self.cursor.x

                    for line_index in range(min_y, max_y+1):
                        line_length = max(5, len(activeFile.raw_lines[line_index]) * self.cursor.char_width)

                        x = 0
                        width = line_length

                        if line_index == min_y:
                            x = min_x * self.cursor.char_width
                            width = line_length - x

                        elif line_index == max_y:
                            x = 0
                            width = max_x * self.cursor.char_width



                        rect_surf = pygame.Surface((width, self.line_height), pygame.SRCALPHA)
                        rect_surf.fill((50, 50, 200, 140))

                        surface.blit(rect_surf, (2 + x, line_index * self.cursor.char_height))





            assert self.line_font is not None, "Attempted to draw the cursor with no loaded font"
            cursor = self.line_font.render("|", True, (235, 235, 235))

            surface.blit(cursor, (cursor.get_width() * self.cursor.x - 2, cursor.get_height() * self.cursor.y))

            if self.possibles_surface is not None:
                surface.blit(
                    self.possibles_surface,
                    (cursor.get_width() * self.cursor.x - 2, cursor.get_height() * (self.cursor.y+1))
                )