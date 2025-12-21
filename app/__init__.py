from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager

app = Flask(__name__)

#Nếu password Mysql không chứa ký tự đặc biệt thì bay đổi thành
#"mysql+pymysql://root:password@localhost/karaoke?charset=utf8mb4"

MYSQL_USER = "Loriss"
MYSQL_PASSWORD = quote("Tuanduy1805@")   # <-- đổi chỗ này
MYSQL_HOST = "Loriss.mysql.pythonanywhere-services.com"
MYSQL_DB = "Loriss$karokedb"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PAGE_SIZE"] = 6

db = SQLAlchemy(session_options={"expire_on_commit": False})
login = LoginManager()

db.init_app(app)
login.init_app(app)
from app import admin