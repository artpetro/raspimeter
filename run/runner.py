# Set the path
import os, sys, getopt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from raspimeter import Raspimeter
from db.mongo_db_manager import MongoDataBaseManager as mdb

raspimeters = {}

def main(argv):
    simulated = False
    
    try:
        opts, args = getopt.getopt(argv, "h:s")
    
    except getopt.GetoptError:
        print 'runner.py -s <simulated>'
        sys.exit(2)
      
    for opt, arg in opts:
        if opt == '-h':
            print 'runner.py [-s]'
            sys.exit()

        elif opt == '-s':
            simulated = True
        
    
    camera_inputs = mdb.getCameraInputs()
    
    for camera_input in camera_inputs:
        rm = Raspimeter(mdb, camera_input, simulated)
        rm.start()
        raspimeters[camera_input.meter.id] = rm


if __name__ == '__main__':
    main(sys.argv[1:])