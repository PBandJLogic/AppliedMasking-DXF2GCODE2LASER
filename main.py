#!/usr/bin/env python3
"""
DXF2TEMPLATE - Replit Entry Point
This file serves as the entry point for Replit deployment.
"""

if __name__ == "__main__":
    from app import app
    app.run(host="0.0.0.0", port=8080, debug=False)
