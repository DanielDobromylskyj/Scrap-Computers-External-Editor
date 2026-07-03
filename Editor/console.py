import pygame
from .console_log import SubMenu
from .console_error import ErrorConsole


class Console:
    def __init__(self, app, fileSystem):
        self.app = app
        self.fs = fileSystem
        self.counter = None

        self.timer = 0

        self.font = pygame.font.SysFont("Monospace", 14)

        self.active_segment = "Output"
        self.segments: dict[str, SubMenu] = {
            "Output": SubMenu(self, self.fs, (240, 240, 240), self.fs.start_print_read, self.fs.fetch_locked_response),
            "Errors": ErrorConsole(self, self.fs),
        }

        self.icons = {
            "Output": "Out",
            "Errors": "Err",
        }

    def change_active_segment(self, new_segment: str):
        assert new_segment in self.segments

        self.active_segment = new_segment
        self.fs.terminate_lock()

    def on_update(self, deltaTime):
        self.timer += deltaTime

        segment = self.segments[self.active_segment]

        if self.timer > segment.update_rate:
            segment.start_read()
            self.timer = 0


    def on_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if event.button == 1:
                if x < 30:
                    button_index = int((y - 5) // (self.font.get_height() + 5))

                    if 0 <= button_index < len(self.segments):
                        self.change_active_segment(list(self.segments.keys())[button_index])

            if x >= 30:
                event.pos = [x - 30, y]

                segment = self.segments[self.active_segment]
                segment.on_click(event)


    def draw(self, surface):
        surface.fill((0, 0, 0, 0))
        pygame.draw.rect(
            surface,
            (25, 25, 25),
            (0, 0, *surface.get_size()),
            border_radius=5
        )

        segment = self.segments[self.active_segment]
        segment.draw_callback(surface)

        i = 0
        for key, icon in self.icons.items():
            bg_colour = (50, 50, 50) if key != self.active_segment else (50, 50, 50)
            primary_colour = (230, 230, 230) if key != self.active_segment else (230, 230, 230)

            text = self.font.render(icon, True, primary_colour)

            pygame.draw.rect(
                surface,
                bg_colour,
                (
                    2, 5 + ((text.get_height() + 5) * i), text.get_width(), text.get_height()
                )
            )

            surface.blit(text, (2, 5 + ((text.get_height() + 5) * i)))
            i += 1







