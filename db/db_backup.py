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
        call(['tar', '-zcvf', archive_path, '-C', tmp_path, '.'])
        call(['rm', '-rf', tmp_path])
        return True
     
    except Exception as e:
        traceback.print_exc()
	return False
    
    
def restore_backup(name):
    return False


def list_backups():
    import datetime
    backups = []
    for file in os.listdir(backup_dir):
        if file.endswith(".tar.gz"):
            timestamp = file.replace('raspimeter_db_', "").replace(".tar.gz", "")
            date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%d-%m-%Y %H:%M:%S')
            size = file_size(os.path.abspath(os.path.join(backup_dir, file)))
            backups.append((date, size, file))
        
    return backups


def delete_backup(name):
    archive_path = os.path.abspath(os.path.join(backup_dir, name))
    try:
        call(['rm', archive_path])
        return True
     
    except Exception as e:
        traceback.print_exc()
    return False


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)
    else:
        print 'not file'
        


if __name__ == '__main__':
    print list_backups()
