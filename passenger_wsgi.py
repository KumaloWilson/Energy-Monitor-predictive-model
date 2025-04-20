import sys
import os

# Add your project directory to the path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# Import your Flask app
from run import app as application

# This is required for WSGI compatibility
application = application