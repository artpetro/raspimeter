from flask import Flask
from flask.ext.mongoengine import MongoEngine

import ConfigParser
import os

from basic_auth import *


class SecuredStaticFlask(Flask):
    @requires_auth
    def send_static_file(self, filename):
        filename = os.normpath('/' + filename).lstrip('/')
        return super(SecuredStaticFlask, self).send_static_file(filename)
            
app = SecuredStaticFlask(__name__, static_url_path='/static')
mongo_db_engine = None

def initMongoEngine(name, password):
    global app
    global mongo_db_engine
    app.config["MONGODB_SETTINGS"] = {'DB': name}
    app.config["SECRET_KEY"] = password
    mongo_db_engine =  MongoEngine(app)

def updateDBConfig(db_name, db_password, user_password):
    config = ConfigParser.ConfigParser()
    config.read('../db/config.cfg')
    config.set('Database', 'name', db_name)
    config.set('Database', 'password', db_password)
    config.set('BasicAuth', 'password', user_password)
    
    with open('../db/config.cfg', 'wb') as configfile:
        config.write(configfile)

    initMongoEngine(db_name, db_password)

config = ConfigParser.ConfigParser()
config.read('../db/config.cfg')
db_name = config.get('Database', 'name')
db_password = config.get('Database', 'password')
initMongoEngine(db_name, db_password)
    

# db_name = 'raspimeter'
# password = 'password'
# initMongoEngine(db_name, password)
