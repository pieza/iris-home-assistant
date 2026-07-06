import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "iris"
    / "command_buttons.py"
)
SPEC = importlib.util.spec_from_file_location("iris_command_buttons", MODULE_PATH)
command_buttons = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = command_buttons
SPEC.loader.exec_module(command_buttons)


class CommandButtonTests(unittest.TestCase):
    def test_telstar_remote_commands_are_exposed_as_buttons(self):
        commands = {button.command for button in command_buttons.REMOTE_BUTTONS}

        self.assertIn("channel_up", commands)
        self.assertIn("channel_down", commands)
        self.assertIn("menu", commands)
        self.assertIn("q_menu", commands)
        self.assertIn("up", commands)
        self.assertIn("down", commands)
        self.assertIn("left", commands)
        self.assertIn("right", commands)
        self.assertIn("ok", commands)
        self.assertIn("netflix", commands)
        self.assertIn("prime_video", commands)
        self.assertIn("youtube", commands)


if __name__ == "__main__":
    unittest.main()
