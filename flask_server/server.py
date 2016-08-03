import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json

from flask import request, send_from_directory, render_template
from flask_mongoengine.wtf import model_form
from flask.ext.wtf import Form

from flask_server import app 
from db.mongo_models import CameraInput
from db.mongo_db_manager import MongoDataBaseManager as db
from run.raspimeter import Raspimeter
import assets

if __name__ == '__main__':
    app.run()
    
@app.route("/")
def index():
    '''
    '''
    meters = []
    
    for meter in db.getMeters():
        meters.append(meter)
        
    # TODO if not configured return appConfig
    
    return render_template('charts.html', meters=meters, show_charts=True)


@app.route("/images_all", methods=['GET'])
def renderImages_TMP():
    '''
    '''
    # Get data from fields
    meter_id = db.getMeters()[0].id#request.args.get('meter_id')
    flag = request.args.get('flag') 

    images = db.getImages(meter_id=meter_id, flag=int(flag))

    return render_template('images_all.html', images=images, meter_id=meter_id)

@app.route("/images", methods=['GET'])
def renderImagesWithPagination():
    '''
    '''
    # Get data from fields
    meter_id = request.args.get('meter_id')
    try:
        flag = int(request.args.get('flag'))
    
    except TypeError:
        flag = -1 #ALL_VALUES
        
    try: 
        page = int(request.args.get('page'))
    
    except TypeError:
        page = 1
    
    pagination = db.getImagesWithPagination(meter_id=meter_id, flag=flag, page=page, per_page=20)
    
    flags = ["OK", "RNV", "NT", "IV", "DNR", "NED", "D", "PE"]
    
    return render_template('images.html', meter_id=meter_id, pagination=pagination, flag=flag, flags=flags, endpoint='renderImagesWithPagination')

@app.route("/meters", methods=['GET'])
def renderMeters():
    '''
    '''
    meters = db.getMeters()
    
    return render_template('meters.html', meters=meters)


@app.route("/settings", methods=('GET', 'POST'))
def renderSettings():
    '''
    '''
    camera_inputs = db.getCameraInputs()
    input_forms = []
    
    for camera_input in camera_inputs:
        CameraInputForm = model_form(CameraInput, Form)
        camera_input_form = CameraInputForm(request.form, camera_input)
    
        if camera_input_form.validate_on_submit():
            camera_input_form.populate_obj(camera_input)
            camera_input = camera_input.save()
        
        input_forms.append(camera_input_form)
        
    return render_template('settings.html', input_forms=input_forms)


@app.route("/get_meter", methods=['GET'])
def getMeter():
    '''
    '''
    meter_id = request.args.get('id')
    meter = db.getMeter(meter_id)

    return meter.to_json()
     

@app.route("/get_meters", methods=['GET'])
def getMeters():
    '''
    '''
    meters = []
    
    for meter in db.getMeters():
        meters.append(json.loads(meter.to_json()))
                 
    return json.dumps(meters)    




@app.route("/get_consumption", methods=['GET'])
def getConsumption():
    '''
    '''
    # Get data from fields
    meter_id = request.args.get('meter_id')
    period = request.args.get('period')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    show_date_as_string = request.args.get('hrf')

    if not period:
        period = 'h'
          
    consumption = db.getPeriodicConsumptions(period=period, 
                                             meter_id=meter_id, 
                                             start_date=start_date, 
                                             end_date=end_date, 
                                             show_date_as_string=show_date_as_string)
     
    return json.dumps(consumption)


@app.route("/get_weather", methods=['GET'])
def getWeather():
    '''
    '''
    # Get data from fields
    meter_id = request.args.get('meter_id')
    period = request.args.get('period')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    show_date_as_string = request.args.get('hrf')
    raw_data = request.args.get('raw')
    
    if not period:
        period = 'h'
    
    weather = db.getWeather(period=period,
                            meter_id=meter_id, 
                            start_date=start_date, 
                            end_date=end_date, 
                            show_date_as_string=show_date_as_string,
                            map_reduce = not bool(raw_data))
     
    return json.dumps(weather)


@app.route("/get_image", methods=['GET'])
def getImage():
    '''
    '''
    return json.dumps(db.getImage(image_id=request.args.get('id')))


@app.route("/get_images", methods=['GET'])
def getImages():
    '''
    '''
    # Get data from fields
    meter_id = request.args.get('meter_id')
    flag = request.args.get('flag')     

    return json.dumps(db.getImages(meter_id=meter_id, flag=int(flag)))


@app.route("/delete_image", methods=['GET'])
def deleteImage():
    '''
    '''
    image_name = request.args.get('image_name')
    value_id = image_name.split('_')[3].split('.')[0]
    
    db.deleteImage(value_id)
    Raspimeter.deleteImage(image_name)
    
#     deleted_from_db = db.deleteMeterValue(value_id)
#     # TODO delete image from file system
    
    return json.dumps({'deleted_from_db': True})


@app.route("/save_digits", methods=['GET'])
def saveDigits():
    '''
    get_digits?image_name=2016-06-05_21-34-30_5753bea9ca18a204c435d117_57549ae6108d4caa345b1fdb.png
                                                    meter_id                meter_value_id
    '''
    image_name = request.args.get('image_name')
    responses = json.loads(str(request.args.get('responses')))
    store_recognized_images = True
    
    new_records_count = Raspimeter.trainKNNAndStoreIntoDB(db, image_name, responses)
    
    # recognize and update value
    meter_image, flag, numeric_value, digits = Raspimeter.readAndRecognizeImage(db, image_name, store_recognized_images)

    return json.dumps({'new_records': new_records_count, 
                       'responses': responses, 
                       'flag': flag, 
                       'numeric_value': numeric_value,
                       'digits': digits})


@app.route("/get_digits", methods=['GET'])
def getDigits():
    '''
    '''
    image_name = request.args.get('image_name')
    
    store_recognized_images = True
    
    return json.dumps(Raspimeter.readAndRecognizeImage(db, image_name, store_recognized_images)[3])


@app.route("/recognize_all", methods=['GET'])
def recognizeAll():
    '''
    '''
    meter_id = request.args.get('meter_id')
    page = int(request.args.get('page'))
    store_recognized_images = True
    success_recogn_counter = Raspimeter.readAndRecognizeAllImages(db, meter_id, page, store_recognized_images)
    
    return json.dumps({'recognized': success_recogn_counter})
    

@app.route('/js/<path:path>')
def send_js(path):
    print path
    return send_from_directory(os.path.join('js', path).replace('\\','/'))