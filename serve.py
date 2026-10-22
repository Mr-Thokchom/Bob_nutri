"""
Production server entry point using Waitress (cross-platform WSGI server).
Run:  python serve.py
"""
from waitress import serve
from app import app
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("NutriBot")

HOST = "0.0.0.0"
PORT = 5000

if __name__ == "__main__":
    log.info("=" * 55)
    log.info("  NutriBot — AI Nutrition Assistant")
    log.info("  Powered by IBM Granite (ibm/granite-4-h-small)")
    log.info("=" * 55)
    log.info("Server starting on http://%s:%d", HOST, PORT)
    log.info("Open your browser at: http://localhost:%d", PORT)
    log.info("Press Ctrl+C to stop.")
    serve(app, host=HOST, port=PORT, threads=4)
