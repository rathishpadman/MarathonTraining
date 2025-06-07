import logging
import os
from app import create_app, socketio

# Configure logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app = create_app()
    
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Start the application with SocketIO
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)
