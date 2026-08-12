# app.py — type this line by line, don't paste
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=8000, use_reloader=True)