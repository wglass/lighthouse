import json
import os


directives_by_section = {}

with open(os.path.join(os.path.dirname(__file__), "directives.json")) as f:
    directives_by_section = json.loads(f.read())
