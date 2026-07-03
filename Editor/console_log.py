import pygame

class SubMenu:
    def __init__(self, host, fileSystem, colour, read_start, read_end, updates_per_second: int = 1):
        self.host = host
        self.colour = colour
        self.fs = fileSystem
        self.update_rate = 1 / updates_per_second

        self.source_start, self.source_end = read_start, read_end
        self.reading = None
        self.last_data = []

    def start_read(self):
        self.reading = False  # Start it going

    def draw_callback(self, surface):
        if self.reading is False:
            self.source_start()
            self.reading = True

        elif self.reading:
            res = self.source_end()

            if res is not False:
                self.reading = None
                self.last_data = res

        self.draw(surface, self.last_data)

    def draw(self, surface, source_data: list):
        if source_data is None:
            return

        source_index = 0
        y_offset = 0

        if len(source_data) > surface.get_height() / self.host.font.get_height():
            source_index = len(source_data) - int(surface.get_height() // self.host.font.get_height())

        while True:
            if len(source_data) <= source_index:
                break

            line = source_data[source_index]

            rect = self.host.font.render(line, True, self.colour)
            surface.blit(rect, (30, y_offset))
            y_offset += rect.get_height()

            source_index += 1

            if y_offset > surface.get_height():
                break


    def on_click(self, event: pygame.event.Event):
        pass