import ast
from pathlib import Path
import unittest


FAN_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "iris" / "fan.py"


class FanCompatibilityTests(unittest.TestCase):
    def test_turn_on_accepts_home_assistant_service_arguments(self):
        module = ast.parse(FAN_PATH.read_text())
        iris_fan = next(
            node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "IrisFan"
        )
        turn_on = next(
            node
            for node in iris_fan.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_turn_on"
        )

        arguments = [argument.arg for argument in turn_on.args.args]
        self.assertEqual(arguments, ["self", "percentage", "preset_mode"])
        self.assertIsNotNone(turn_on.args.kwarg)

    def test_oscillate_uses_the_profile_command(self):
        module = ast.parse(FAN_PATH.read_text())
        iris_fan = next(
            node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "IrisFan"
        )
        oscillate = next(
            node
            for node in iris_fan.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_oscillate"
        )

        self.assertEqual([argument.arg for argument in oscillate.args.args], ["self", "oscillating"])


if __name__ == "__main__":
    unittest.main()
