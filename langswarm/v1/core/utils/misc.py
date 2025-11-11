from io import StringIO
from html.parser import HTMLParser

class StripTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

class SafeMap(dict):
    def __missing__(self, key):
        return f'{{{key}}}'
