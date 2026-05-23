# Project Organization Tasks

- [x] Create /templates directory
- [x] Move index.html to /templates
- [x] Create /static directory
- [x] Move style.css to /static
- [x] Move script.js to /static
- [x] Edit index.html to update CSS and JS links to /static paths
- [x] Create /src directory
- [x] Move Iris.py to /src
- [x] Verify no path updates needed in Iris.py (Flask handles /templates and /static automatically)
- [x] Clean up code in Iris.py (fix indentation, remove duplicates, fix bugs)

# Full Stack Integration Tasks

- [x] Create .env file with OpenAI API key
- [x] Install pymongo and python-dotenv dependencies
- [x] Set up MongoDB connection in Flask app
- [x] Update Flask app to store conversation history in MongoDB
- [x] Integrate voice input (SpeechRecognition API) into web interface
- [x] Integrate voice output (SpeechSynthesis API) into web interface
- [x] Update Iris.py to use environment variables and fix bugs
- [x] Replace OpenAI with Cohere AI
- [x] Test the full stack app
- [x] Add voice input/output buttons to HTML
- [x] Update JavaScript for voice functionality
- [x] Update CSS for button styling

# Code Refactoring Tasks

- [x] Create config.py for environment variables and constants
- [x] Create speech.py for speech recognition and TTS functions
- [x] Create ai.py for OpenAI integration
- [x] Create commands.py for specific command handlers (calc, browse)
- [x] Create database.py for MongoDB setup and operations
- [x] Create app.py for Flask app and routes
- [x] Refactor Iris.py to import from modules and run the app
- [x] Test refactored code (Flask server running successfully)
