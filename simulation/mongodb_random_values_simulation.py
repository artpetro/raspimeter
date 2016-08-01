'''
Created on 29.05.2016

@author: Artem
'''
# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import timedelta
import datetime
import random
import pickle

from db.mongo_db_manager import MongoDataBaseManager as mdb
from calendar import month

from db.mongo_db_manager import MeterValue, Consumption

SIMULATED_METER_ID = mdb.getMeters()[0].id#'5753bea9ca18a204c435d117'

def createRandomValues(years=(2016,), minutes_delta=1):
    
    utc_now = datetime.datetime.utcnow()
    date = utc_now.replace(year=years[0], day=1)
    date_end = date.replace(year=years[-1], month=12, day=31) 
    
    days = (date_end - date).days
         
    minutes = days * 24 * 60
    value = 0
    data_source = []
    
    #TODO utc offset
     
    for i in range(0, minutes, minutes_delta):
        data_source.append({'meter_id': SIMULATED_METER_ID, 'timestamp': date, 'numeric_value': value, 'flag': 0})
        date += timedelta(minutes=(minutes_delta + random.randrange(5))) # +-5 min
        value += random.randrange(10)
        
    return data_source
    

def insertRandomValues(data_source, bulk=False, max_number=0):

    count = 0
    for value in data_source:
            
        if count < max_number:
            print count
            mdb.storeMeterValue(meter_id=value['meter_id'], timestamp=value['timestamp'], flag=0, numeric_value=value['numeric_value'])

        count += 1
        
    

if __name__ == '__main__':
    
#     MeterValue.drop_collection() 
#     Consumption.drop_collection() 
#     
#     start = datetime.datetime.now()
#     data = createRandomValues((2016,), minutes_delta=30)
#     print len(data)
#      
#     insertRandomValues(data, max_number=10)
#     
#     print 'inserted in %s' % (datetime.datetime.now() - start)

    pass
