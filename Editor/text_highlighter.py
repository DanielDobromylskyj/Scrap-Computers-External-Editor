class SyntaxHighlighter:
    LANGUAGE = "general"
    DEFAULT_COLOUR = (240, 240, 240)

    KEYWORDS = {}

    def highlight(self, text):
        return [(text, self.DEFAULT_COLOUR)]