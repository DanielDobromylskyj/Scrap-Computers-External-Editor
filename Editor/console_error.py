import pygame

from .console_log import SubMenu


class ErrorConsole(SubMenu):
    def __init__(self, host, fileSystem):
        super().__init__(host, fileSystem, (250, 20, 20), fileSystem.start_error_read, fileSystem.fetch_locked_response)
        self.last_source = []

    def in_file_format(self, line):
        if not line.startswith("[path \""):
            return False

        if not line.endswith(":"):
            return False

        end_x1 = line.split('"')[1]
        end_x2 = line.split(":")[1]

        return 6, 8+len(end_x1), 10+len(end_x1), 10+len(end_x1)+len(end_x2)

    def on_click(self, event: pygame.event.Event):
        if event.button == 1:
            line: str | None = self.draw(None, self.last_source, detect_click=True, mx=event.pos[0], my=event.pos[1])

            if line is not None:
                slices = self.in_file_format(line)

                if not isinstance(slices, tuple):
                    return

                path = line[slices[0]+1:slices[1]-1]
                line_num = int(line[slices[2]:slices[3]]) - 1

                if "..." in path:
                    print("[WARNING] Cant load file, out of project scope")
                    return


                editor = self.host.app.editorView
                possible_index = editor.is_file_open(path)


                if possible_index is not None:
                    editor.open_file(possible_index)

                else:
                    fo = self.fs.file_object_from_path(path)
                    editor.add_file(fo)

                editor.lines_scrolled = max(0, line_num - 5)
                editor.cursor.x = 0
                editor.cursor.y = line_num



    def draw(self, surface: pygame.Surface | None, source_data: list, detect_click=False, mx=0, my=0) -> str | None:
        self.last_source = source_data

        if source_data is None:
            print("[WARNING] Fail to draw error log, Failed to fetch source data, try and reload the error console")
            return None

        if len(source_data) > 0:
            source_data = source_data[0].replace(": ", ":\n").split("\n")

        if surface is None and detect_click is False:
            raise ValueError("No Surface and Not detecting clicks")

        source_index = 0
        y_offset = 0

        if not detect_click:
            if len(source_data) > surface.get_height() / self.host.font.get_height():
                source_index = len(source_data) - int(surface.get_height() // self.host.font.get_height())

        while True:
            if len(source_data) <= source_index:
                break

            line = source_data[source_index]
            data = self.in_file_format(line)

            if data is False:
                rect = self.host.font.render(line, True, self.colour)
                if not detect_click:
                    surface.blit(rect, (30, y_offset))
                y_offset += rect.get_height()
            else:
                start_x1, end_x1, start_x2, end_x2 = data
                largest_y = 0

                current_x_offset = 30
                rect = self.host.font.render(line[:start_x1], True, self.colour)

                if not detect_click:
                    surface.blit(rect, (current_x_offset, y_offset))
                else:
                    if ((current_x_offset < mx < current_x_offset+rect.get_width()) and
                            (y_offset < my < y_offset + rect.get_height())):
                        return line

                largest_y = max(largest_y, rect.get_height())
                current_x_offset += rect.get_width()

                rect = self.host.font.render(line[start_x1:end_x1], True, (80, 209, 216))

                if not detect_click:
                    surface.blit(rect, (current_x_offset, y_offset))
                else:
                    if ((current_x_offset < mx < current_x_offset+rect.get_width()) and
                            (y_offset < my < y_offset + rect.get_height())):
                        return line

                largest_y = max(largest_y, rect.get_height())
                current_x_offset += rect.get_width()

                rect = self.host.font.render(line[end_x1:start_x2], True, self.colour)

                if not detect_click:
                    surface.blit(rect, (current_x_offset, y_offset))
                else:
                    if ((current_x_offset < mx < current_x_offset+rect.get_width()) and
                            (y_offset < my < y_offset + rect.get_height())):
                        return line

                largest_y = max(largest_y, rect.get_height())
                current_x_offset += rect.get_width()

                rect = self.host.font.render(line[start_x2:end_x2], True, (80, 209, 216))

                if not detect_click:
                    surface.blit(rect, (current_x_offset, y_offset))
                else:
                    if ((current_x_offset < mx < current_x_offset+rect.get_width()) and
                            (y_offset < my < y_offset + rect.get_height())):
                        return line

                largest_y = max(largest_y, rect.get_height())
                current_x_offset += rect.get_width()

                rect = self.host.font.render(line[end_x2:], True, self.colour)
                if not detect_click:
                    surface.blit(rect, (current_x_offset, y_offset))
                else:
                    if ((current_x_offset < mx < current_x_offset+rect.get_width()) and
                            (y_offset < my < y_offset + rect.get_height())):
                        return line

                largest_y = max(largest_y, rect.get_height())
                current_x_offset += rect.get_width()


                y_offset += largest_y


            source_index += 1

            if not detect_click and y_offset > surface.get_height():
                break