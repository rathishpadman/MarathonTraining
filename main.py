import logging
import os
from dotenv import load_dotenv
from app import create_app, socketio

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app at module level for gunicorn
app = create_app()

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Start the application with SocketIO
    socketio.run(app, host="0.0.0.0", port=port, debug=True, use_reloader=False, log_output=True)
