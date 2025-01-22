from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# Secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key'

# Import routes
import routes

if __name__ == '__main__':
    app.run(debug=True)

