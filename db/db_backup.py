import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import traceback
from subprocess import call

backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'flask_server', 'static', 'db_backups'))

def create_backup():
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
    
    
def restore_backup(name):
    return False


def list_backups():
    backups = []
    for file in os.listdir(backup_dir):
        if file.endswith(".tar.gz"):
            backups.append(file)
        
    return backups


def delete_backup(name):
    archive_path = os.path.abspath(os.path.join(backup_dir, name))
    try:
        call(['rm', archive_path])
        return True
     
    except Exception as e:
        traceback.print_exc()
    return False



if __name__ == '__main__':
    list_backups()
