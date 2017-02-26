import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import traceback
from subprocess import call

backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'flask_server', 'static', 'db_backups'))

def backup():
    #make backup to tmp dir raspimeter_db_timestamp
    tmp_dir = 'raspimeter_db_%s' % int(round(time.time()))
    tmp_path = os.path.abspath(os.path.join(backup_dir, tmp_dir))
    archive_path = os.path.abspath(os.path.join(backup_dir, '%s.tar.gz' % tmp_dir))
    try:
        call(['mongodump', '--out', tmp_path])
        call(['tar', '-zcvf', archive_path, tmp_path])
        call(['rm', '-rf', tmp_path])
        return True
     
    except Exception as e:
        traceback.print_exc()
	return False
    
def restore():
    pass

if __name__ == '__main__':
    backup()
