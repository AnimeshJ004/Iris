import sys
import os

# Add the project root and 'src' directory to Python's module search path.
# This ensures both 'src.X' and bare 'X' imports work everywhere.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
src_dir = os.path.join(root_dir, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# root_dir is now in sys.path, so 'src' is a resolvable package.
# This single import works both locally and on Vercel.
from src.app import app  # noqa: E402

# Vercel requires the Flask 'app' instance to be exposed at the module level.
if __name__ == "__main__":
    app.run(debug=True)
