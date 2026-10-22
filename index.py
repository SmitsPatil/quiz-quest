"""
Root WSGI Entry Point for Flask on Vercel
"""
from app import app

if __name__ == "__main__":
    app.run()
