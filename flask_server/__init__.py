from flask import Flask
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)

app.config["MONGODB_SETTINGS"] = {'DB': "raspimeter"}
app.config["SECRET_KEY"] = "KeepThisS3cr3t"

mongo_db_engine = MongoEngine(app)

    
    