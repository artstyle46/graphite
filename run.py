import os

from app import app, setup_app

setup_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)