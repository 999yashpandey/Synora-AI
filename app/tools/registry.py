from typing import Callable


class ToolRegistry:

    def __init__(self):
        self.tools: dict[str, Callable] = {}

    def register(self, name: str, function: Callable):
        self.tools[name] = function

    def execute(self, name: str, **kwargs):

        if name not in self.tools:
            return f"Tool '{name}' is not available."

        try:
            return self.tools[name](**kwargs)

        except Exception as error:
            return f"Tool '{name}' failed: {error}"

    def list_tools(self):
        return list(self.tools.keys())