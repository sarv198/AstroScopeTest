"""
WSGI entry point for Vercel deployment
"""
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    app = create_app()
except Exception as e:
    print(f"Error creating app: {e}")
    # Create a minimal Flask app as fallback
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def fallback():
        return f"App creation failed: {str(e)}"

if __name__ == "__main__":
    app.run()
