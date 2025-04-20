import sys
import os
from dotenv import load_dotenv

# Set OpenBLAS thread limit before any imports that might use it
os.environ['OPENBLAS_NUM_THREADS'] = '4'  # Limit to 4 threads, adjust as needed

# Load environment variables from .env file
load_dotenv()

# Add your project directory to the path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# Import your Flask app from run.py
from run import app as application