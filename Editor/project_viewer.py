import os
import pygame

from backend import FileSystem

class ProjectView:
    COLOUR_MODIFIED = (37, 161, 219)
    COLOUR_SAVED = (46, 191, 17)
    COLOUR_DEFAULT = (240, 240, 240)

    X_STEP = 10

    def __init__(self, app, filesystem: FileSystem):
        self.app = app
        self.filesystem = filesystem
        self.cached_layout = {}
        self.lua_files = []
        self.line_lookup = []

        self.last_frame = None
        self.should_redraw = True

        self.font = pygame.font.SysFont("Monospace", 14)
        self.font_height = self.font.get_height()

        self.app.blit_text("Fetching Project Files...")
        self.reload_cache()

        self.buttons = {
            "new_file": [
                [0, 0, 0, 0],
                self.request_new_file
            ]
        }


    def _reload_cache(self, cwd, path):
        contents = self.filesystem.list_dir(path)
        for fileObject in contents:
            if fileObject.is_file:
                cwd[fileObject.name] = {
                    "modified": False,
                    "contents": fileObject,
                    "type": "file"
                }

                if fileObject.path.endswith(".lua"):
                    self.lua_files.append(fileObject)

            if fileObject.is_directory:
                sub_cwd = {}
                cwd[fileObject.name] = {
                    "expanded": False,
                    "contents": sub_cwd,
                    "type": "directory",
                    "obj": fileObject
                }

                self._reload_cache(sub_cwd, os.path.join(path, fileObject.name).replace("\\", "/"))

    def reload_cache(self):
        self.cached_layout = {}
        self.lua_files = []

        if self.filesystem.connected:
            self._reload_cache(self.cached_layout, "/")

    def __sub_draw(self, surface, cwd, y_offset, x_offset):
        for key, value in cwd.items():
            if value["type"] == "file":
                colour = self.COLOUR_MODIFIED if value["modified"] else self.COLOUR_SAVED
                text = self.font.render(key, True, colour)

                surface.blit(text, (x_offset, y_offset))
                y_offset += text.get_height()
                self.line_lookup.append(value)

            else:
                colour = self.COLOUR_DEFAULT
                text = self.font.render(key, True, colour)
                surface.blit(text, (x_offset, y_offset))

                y_offset += text.get_height()
                self.line_lookup.append(value)

                if value["expanded"]:
                    y_offset = self.__sub_draw(surface, value["contents"], y_offset, x_offset + self.X_STEP)

        return y_offset

    def _redraw(self, surface):
        surface.fill((0, 0, 0, 0))
        pygame.draw.rect(
            surface,
            (20, 20, 20),
            (0, 0, *surface.get_size()),
            border_radius=5
        )

        text = self.font.render("+", True, (240, 240, 240))

        pygame.draw.rect(
            surface,
            (40, 40, 40),
            (surface.get_width() - (text.get_height() + 3), 2, text.get_height() + 1, text.get_height() + 2),
            border_radius=3
        )

        bx, by = surface.get_width() - (text.get_height() + 4) + (text.get_height() - text.get_width()) / 2 + 1, 3
        surface.blit(text, (bx, by))
        self.buttons["new_file"][0] = [ bx, by, text.get_width(), text.get_height()]

        self.line_lookup = []
        self.__sub_draw(surface, self.cached_layout, self.font_height + 5, 5)

    def request_new_file(self):
        self.app.open_input_box(
            "New File Path",
            "Please enter a path",
            self.new_file,
            starting_text="Not Implemented Yet",
            width=300
        )

    def new_file(self, path):
        print("New Files Not Implemented. Go bother someone else")


    def click(self, x, y):
        line_index = (y - (self.font_height + 5)) // self.font_height

        if 0 <= line_index < len(self.line_lookup):
            file = self.line_lookup[line_index]

            if file["type"] == "file":
                self.app.editorView.add_file(file["contents"])
            else:
                file["expanded"] = not file["expanded"]
                self.should_redraw = True

        else:
            for [bx, by, bw, bh], callback in self.buttons.values():
                if bx < x < bx + bw and by < y < by + bh:
                    callback()
                    return


    def draw(self, surface):
        if not self.last_frame:
            self.should_redraw = True

        elif surface.get_size() != self.last_frame.get_size():
            self.should_redraw = True

        if self.should_redraw:
            self._redraw(surface)

            self.should_redraw = False
            self.last_frame = surface

        surface.blit(self.last_frame, (0, 0))
