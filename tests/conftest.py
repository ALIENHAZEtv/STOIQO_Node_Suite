import os
import sys

suite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if suite_root not in sys.path:
    sys.path.insert(0, suite_root)

def pytest_configure(config):
    nodes_dir = os.path.join(suite_root, "nodes")
    if "nodes" in sys.modules:
        n_mod = sys.modules["nodes"]
        if not hasattr(n_mod, "__path__"):
            n_mod.__path__ = [nodes_dir]
        elif nodes_dir not in n_mod.__path__:
            n_mod.__path__.insert(0, nodes_dir)
