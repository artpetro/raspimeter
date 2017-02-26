import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_server import app
import time

backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'flask_server', 'static', 'db_backups'))

def backup():
    #make backup to tmp dir raspimeter_db_timestamp
    tmp_dir = os.path.abspath(os.path.join(backup_dir, 'raspimeter_db_%s' % int(round(time.time()))))
    try:
        call(['mongodump', '--out', tmp_dir])
        #make tar.gz
        #remove tmp dir
        print 'OK'
     
    except Exception as e:
        message = "ERROR"
        traceback.print_exc()
    
def restore():
    pass

if __name__ == '__main__':
    backup()