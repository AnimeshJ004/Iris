import sys
import os

# Add src directory to path so modules can find each other
sys.path.insert(0, os.path.dirname(__file__))

from app import app

if __name__ == "__main__":
    print("\n  🔮 Iris AI Assistant is starting...")
    print("  📍 Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, use_reloader=False)
