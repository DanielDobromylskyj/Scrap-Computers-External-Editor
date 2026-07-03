import pygame

from backend import FileSystem
from .project_viewer import ProjectView
from .code_editor import CodeEditor
from .console import Console

pygame.init()


class App:
    def __init__(self, mod_path):
        self.screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)
        pygame.display.set_caption("SC/SM External Editor - Real Time Editing")

        self.clock = pygame.time.Clock()

        self.blit_text("Creating File System...")

        self.filesystem = FileSystem(mod_path)

        self.projectView = ProjectView(self, self.filesystem)
        self.editorView = CodeEditor(self, self.projectView)
        self.consoleView = Console(self, self.filesystem)

        self.running = False

        self.top_header_height = 30
        self.window_gap_size = 5
        self.projectViewRatio = 0.25
        self.consoleViewRatio = 0.3

        # Top bar - One day
        self.topbar_location = []

        self.topbar = {
            "File": {
                "New File": None,
                "Save": None
            }
        }

        # Input Stuff
        self.input_font = pygame.font.SysFont("Monospace", 18)
        self.input_char_width = self.input_font.render("#", True, (0, 0, 0)).get_width()
        self.input_boxes = []
        self.close_button_bounds = None


        # Setup
        self.auto_connect()

    def blit_text(self, text):
        self.screen.fill((30, 30, 30))
        font = pygame.font.SysFont("Monospace", 20)
        rect = font.render(text, True, (255, 255, 255))
        self.screen.blit(rect, ((self.screen.get_width() - rect.get_width()) / 2, (self.screen.get_height() - rect.get_height()) / 2))
        pygame.display.flip()

    def on_filesystem_connect(self):
        self.projectView.reload_cache()
        self.editorView.init_analyzer()
        self.filesystem.reset_print_log()

    def auto_connect(self):
        cmps = self.filesystem.get_available_computers()
        assert cmps, "No computers found"

        if len(cmps) == 1:
            print(f"Found one computer, Auto connecting to #{int(cmps[0])}")
            pygame.display.set_caption(f"SC/SM External Editor - Real Time Editing [CMP #{int(cmps[0])}]")
            self.filesystem.select_computer(cmps[0])
        else:
            while True:
                print("Found Many Computers, Please Select Your ID From The List Below")
                print("\n".join(f"> {int(cmp)}" for cmp in cmps))
                inp = input("> ")

                if inp.isdigit() and int(inp) in cmps:
                    self.filesystem.select_computer(int(inp))
                    pygame.display.set_caption(f"SC/SM External Editor - Real Time Editing [CMP #{inp}]")
                    break

                else:
                    print("Invalid Input")

        self.on_filesystem_connect()

    def create_project_surface(self):
        return pygame.Surface(
            ((self.screen.get_width() - self.window_gap_size) * self.projectViewRatio,
                  (self.screen.get_height() - self.top_header_height) * (1 - self.consoleViewRatio)),
                pygame.SRCALPHA
        )

    def create_editor_surface(self):
        return pygame.Surface(
            ((self.screen.get_width() - self.window_gap_size) * (1 - self.projectViewRatio),
                  (self.screen.get_height() - self.top_header_height) * (1 - self.consoleViewRatio)),
                pygame.SRCALPHA
        )

    def create_console_surface(self):
        return pygame.Surface(
            (self.screen.get_width(),
                  (self.screen.get_height() - self.top_header_height) * self.consoleViewRatio - self.window_gap_size),
                pygame.SRCALPHA
        )

    def open_input_box(self, title: str, text: str, callback: object, starting_text: str | None = None,
                       width: int | None = None, height: int | None = None):
        self.input_boxes.append({
            "title": title,
            "text": text,
            "callback": callback,
            "data": starting_text if starting_text else "",

            "shape": (
                width if width else max(len(title), len(text)) * self.input_char_width + 10,
                height if height else 4 * self.input_font.get_height() + 20
            )
        })

    def render_input_boxes(self):
        for input_box in self.input_boxes:
            surface = pygame.Surface(input_box["shape"], pygame.SRCALPHA)
            offset_x = (self.screen.get_width() - surface.get_width()) / 2
            offset_y = (self.screen.get_height() - surface.get_height()) / 2

            pygame.draw.rect(
                surface,
                (35, 35, 35),
                (0, 0, *surface.get_size()),
                border_radius=6
            )


            pygame.draw.rect(
                surface,
                (50, 50, 50),
                (0, 0, surface.get_width(), self.input_font.get_height()),
                border_top_left_radius=6,
                border_top_right_radius=6
            )

            title_rect = self.input_font.render(input_box["title"], True, (255, 255, 255))
            surface.blit(title_rect, (4, 0))

            desc_rect = self.input_font.render(input_box["text"], True, (255, 255, 255))
            surface.blit(desc_rect, (4, self.input_font.get_height() + 3))

            pygame.draw.rect(
                surface,
                (25, 25, 25),
                (4, (self.input_font.get_height()*2 + 5), surface.get_width() - 8, self.input_font.get_height() + 4),
                border_radius=3
            )

            input_rect = self.input_font.render(input_box["data"], True, (255, 255, 255))
            surface.blit(input_rect, (4, self.input_font.get_height()*2 + 7))

            button_rect = self.input_font.render("Done", True, (255, 255, 255))

            pygame.draw.rect(
                surface,
                (50, 50, 50),
                (
                        (surface.get_width() - button_rect.get_width()) / 2 - 2, self.input_font.get_height() * 3 + 15 - 2,
                        button_rect.get_width() + 4, button_rect.get_height() + 4
                ),
                border_radius=3
            )

            surface.blit(button_rect, ((surface.get_width() - button_rect.get_width()) / 2, self.input_font.get_height() * 3 + 15))
            self.close_button_bounds = (
                (
                    offset_x + (surface.get_width() - button_rect.get_width()) / 2,
                    offset_y + self.input_font.get_height() * 3 + 15
                ),
                button_rect.get_size()
            )

            pygame.draw.rect(
                surface,
                (120, 120, 120),
                (0, 0, *surface.get_size()),
                border_radius=6, width=1
            )

            self.screen.blit(
                surface, (offset_x, offset_y)
            )

    def close_top_input(self):
        self.close_button_bounds = None

        if len(self.input_boxes) > 0:
            input_box = self.input_boxes.pop(-1)

            input_box["callback"](input_box["data"])



    def onclick(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.close_button_bounds is not None and event.button == 1:
                [x, y], [w, h] = self.close_button_bounds
                if x < mx < x + w and y < my < y + h:
                    self.close_top_input()
                    return

        if "pos" in event.dict:
            x, y = event.pos

            if 0 <= x < (self.screen.get_width() - self.window_gap_size) * self.projectViewRatio and self.top_header_height <= y < (self.screen.get_height() * (1 - self.consoleViewRatio) + self.window_gap_size*2):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.projectView.click(x, y - self.top_header_height)

            elif (self.screen.get_width() - self.window_gap_size) * self.projectViewRatio <= x and self.top_header_height <= y < (self.screen.get_height() * (1 - self.consoleViewRatio) + self.window_gap_size*2):
                event.pos = (event.pos[0] - ((self.screen.get_width() - self.window_gap_size) * self.projectViewRatio), event.pos[1] - self.top_header_height)
                self.editorView.on_click(event)

            elif y > (self.screen.get_height() * (1 - self.consoleViewRatio) + (self.window_gap_size*2)):
                event.pos = (event.pos[0],
                             event.pos[1] - (self.screen.get_height() * (1 - self.consoleViewRatio) + self.window_gap_size*2))
                self.consoleView.on_click(event)

        else:
            self.editorView.on_click(event)

    def run(self):
        self.running = True

        while self.running:
            rawTime = self.clock.get_time()
            deltaTime = rawTime / 1000 if rawTime > 0 else 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                    self.onclick(event)

                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    self.editorView.onkey_event(event)

            self.screen.fill((40, 40, 40))

            project_surface = self.create_project_surface()
            self.projectView.draw(project_surface)
            self.screen.blit(project_surface, (0, self.top_header_height))

            editor_surface = self.create_editor_surface()
            self.editorView.on_update(deltaTime)
            self.editorView.draw(editor_surface)
            self.screen.blit(editor_surface, (project_surface.get_width() + self.window_gap_size, self.top_header_height))

            console_surface = self.create_console_surface()
            self.consoleView.on_update(deltaTime)
            self.consoleView.draw(console_surface)
            self.screen.blit(console_surface, (0, self.top_header_height+editor_surface.get_height() + self.window_gap_size))

            self.render_input_boxes()

            pygame.display.flip()
            self.clock.tick(60)

