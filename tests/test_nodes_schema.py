"""
[STOIQO] Custom Nodes Schema & ComfyUI Specification Compliance Test Suite
Validates that every registered custom node adheres strictly to ComfyUI specification standards:
- INPUT_TYPES classmethod structure (required/optional dicts)
- RETURN_TYPES tuple validity
- FUNCTION string pointing to an existing callable method
- CATEGORY non-empty string
- Mapping consistency between NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS
"""

import unittest
import sys
import os

import importlib.util

suite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if suite_root not in sys.path:
    sys.path.insert(0, suite_root)

_spec = importlib.util.spec_from_file_location(
    "stoiqo_nodes_pkg",
    os.path.join(suite_root, "nodes", "__init__.py"),
    submodule_search_locations=[os.path.join(suite_root, "nodes")],
)
_stoiqo_nodes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_stoiqo_nodes)
NODE_CLASS_MAPPINGS = _stoiqo_nodes.NODE_CLASS_MAPPINGS
NODE_DISPLAY_NAME_MAPPINGS = _stoiqo_nodes.NODE_DISPLAY_NAME_MAPPINGS


class TestComfyUINodeSchemaCompliance(unittest.TestCase):
    """Verifies that all STOIQO custom nodes conform to ComfyUI architectural specifications."""

    def test_mappings_non_empty(self):
        """Verifies that the suite exports registered node classes."""
        self.assertGreater(len(NODE_CLASS_MAPPINGS), 0, "NODE_CLASS_MAPPINGS must not be empty.")
        self.assertGreater(len(NODE_DISPLAY_NAME_MAPPINGS), 0, "NODE_DISPLAY_NAME_MAPPINGS must not be empty.")

    def test_display_names_correspondence(self):
        """Verifies that every node class has a corresponding human-readable display name."""
        for node_id, cls in NODE_CLASS_MAPPINGS.items():
            self.assertIn(
                node_id,
                NODE_DISPLAY_NAME_MAPPINGS,
                f"Node ID '{node_id}' ({cls.__name__}) is missing in NODE_DISPLAY_NAME_MAPPINGS."
            )
            display_name = NODE_DISPLAY_NAME_MAPPINGS[node_id]
            self.assertTrue(
                isinstance(display_name, str) and len(display_name.strip()) > 0,
                f"Display name for '{node_id}' must be a non-empty string."
            )

    def test_node_class_specifications(self):
        """Validates INPUT_TYPES, RETURN_TYPES, FUNCTION, and CATEGORY for all classes."""
        for node_id, cls in NODE_CLASS_MAPPINGS.items():
            # 1. INPUT_TYPES classmethod
            self.assertTrue(
                hasattr(cls, "INPUT_TYPES"),
                f"Node class '{cls.__name__}' must implement INPUT_TYPES classmethod."
            )
            try:
                input_types = cls.INPUT_TYPES()
            except Exception as e:
                self.fail(f"Calling {cls.__name__}.INPUT_TYPES() raised an exception: {e}")

            self.assertIsInstance(
                input_types, dict,
                f"{cls.__name__}.INPUT_TYPES() must return a dictionary."
            )
            self.assertIn(
                "required", input_types,
                f"{cls.__name__}.INPUT_TYPES() must contain a 'required' dictionary."
            )
            self.assertIsInstance(
                input_types["required"], dict,
                f"{cls.__name__}.INPUT_TYPES()['required'] must be a dictionary."
            )

            # 2. RETURN_TYPES tuple
            self.assertTrue(
                hasattr(cls, "RETURN_TYPES"),
                f"Node class '{cls.__name__}' must define RETURN_TYPES attribute."
            )
            return_types = getattr(cls, "RETURN_TYPES")
            self.assertIsInstance(
                return_types, tuple,
                f"{cls.__name__}.RETURN_TYPES must be a tuple, found {type(return_types).__name__}."
            )

            # 3. FUNCTION attribute
            self.assertTrue(
                hasattr(cls, "FUNCTION"),
                f"Node class '{cls.__name__}' must define FUNCTION attribute."
            )
            func_name = getattr(cls, "FUNCTION")
            self.assertIsInstance(
                func_name, str,
                f"{cls.__name__}.FUNCTION must be a string."
            )
            self.assertTrue(
                hasattr(cls, func_name),
                f"Node class '{cls.__name__}' declares FUNCTION '{func_name}', but method does not exist on class."
            )
            self.assertTrue(
                callable(getattr(cls, func_name)),
                f"Attribute '{func_name}' on '{cls.__name__}' must be callable."
            )

            # 4. CATEGORY attribute
            self.assertTrue(
                hasattr(cls, "CATEGORY"),
                f"Node class '{cls.__name__}' must define CATEGORY attribute."
            )
            category = getattr(cls, "CATEGORY")
            self.assertIsInstance(
                category, str,
                f"{cls.__name__}.CATEGORY must be a string."
            )
            self.assertTrue(
                len(category.strip()) > 0,
                f"{cls.__name__}.CATEGORY must not be empty."
            )

    def test_js_settings_drawer_widget_mappings(self):
        """Verifies that all node classes and widget names in src_js/utils/settingsDrawer.js match Python INPUT_TYPES."""
        import re
        drawer_js = os.path.join(suite_root, "src_js", "utils", "settingsDrawer.js")
        self.assertTrue(os.path.isfile(drawer_js), "settingsDrawer.js must exist.")
        with open(drawer_js, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract top-level keys of NODE_UX_SPECS (Stoiqo*Node / Stoiqo*)
        spec_blocks = re.findall(r"^\s{4}(Stoiqo\w+):\s*\{(.*?)^\s{4}\},", content, flags=re.MULTILINE | re.DOTALL)
        self.assertGreaterEqual(len(spec_blocks), 15)

        for cls_name, block in spec_blocks:
            self.assertIn(cls_name, NODE_CLASS_MAPPINGS, f"JS UX spec references unknown node class '{cls_name}'")
            cls = NODE_CLASS_MAPPINGS[cls_name]
            inp = cls.INPUT_TYPES()
            all_inputs = set(inp.get("required", {}).keys()) | set(inp.get("optional", {}).keys())

            # Extract advanced array strings
            adv_match = re.search(r"advanced:\s*\[(.*?)\]", block, flags=re.DOTALL)
            if adv_match:
                adv_widgets = re.findall(r'"(\w+)"', adv_match.group(1))
                for w in adv_widgets:
                    self.assertIn(w, all_inputs, f"Node '{cls_name}' advanced widget '{w}' not in INPUT_TYPES: {sorted(all_inputs)}")


if __name__ == "__main__":
    unittest.main()

