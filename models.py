from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# Initialize the SQLAlchemy object
db = SQLAlchemy()

# ===================== USER MODEL =======================
class User(db.Model , UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def is_active(self):
        return True  

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.id)  # Return the user's id as a string

# ===================== CHAT HISTORY MODEL =======================
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_input = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(150), nullable=True)  
    
    user = db.relationship('User', backref=db.backref('chats', lazy=True))

    def __repr__(self):
        return f"<ChatHistory {self.id} - {self.timestamp}>"
