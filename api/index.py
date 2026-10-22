"""
Vercel Serverless Function Entry Point for Quiz Quest
Exposes the Flask WSGI application instance 'app' for Vercel Python runtime.
"""

import sys
import os

# Add root directory to sys.path so modules and services can be found
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

# Vercel WSGI entry point
# 'app' is the Flask WSGI callable
