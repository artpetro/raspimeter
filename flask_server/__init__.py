from flask import Flask
from flask.ext.mongoengine import MongoEngine

import ConfigParser

app = Flask(__name__)
mongo_db_engine = None

def initMongoEngine(name, password):
    global app
    global mongo_db_engine
    app.config["MONGODB_SETTINGS"] = {'DB': name}
    app.config["SECRET_KEY"] = password
    mongo_db_engine =  MongoEngine(app)
    
def updateDBConfig(name, password):
    config = ConfigParser.ConfigParser()
    config.read('../db/config.cfg')
    config.set('Database', 'name', name)
    config.set('Database', 'password', password)
        
    with open('../db/config.cfg', 'wb') as configfile:
        config.write(configfile)
        
    initMongoEngine(name, password)
    
    

config = ConfigParser.ConfigParser()
config.read('../db/config.cfg')
    
db_name = config.get('Database', 'name')
password = config.get('Database', 'password')

initMongoEngine(db_name, password)
    

#app.config["MONGODB_SETTINGS"] = {'DB': "raspimeter"}
#app.config["SECRET_KEY"] = "KeepThisS3cr3t"

    
    