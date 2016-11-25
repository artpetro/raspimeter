import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import cPickle
from subprocess import call
import traceback

from flask import request, send_from_directory, render_template, redirect
from flask_mongoengine.wtf import model_form
from flask.ext.wtf import Form

from flask_server import app 
from db.mongo_models import CameraInput, MeterSettings, MeterImageSettings, KNNSettings
from db.mongo_db_manager import MongoDataBaseManager as db
from run.raspimeter import Raspimeter
import assets
from basic_auth import *

if __name__ == '__main__':
    app.run()
    
    
@app.route("/")
@requires_auth
def index():
    '''
    '''
    if app.config["MONGODB_SETTINGS"]['DB'] == '':
        return redirect("/settings", code=302)
    
    meters = []
    
    for meter in db.getMeters():
        meters.append(meter)
        
    return render_template('charts.html', meters=meters, show_charts=True)


@app.route("/images", methods=['GET'])
@requires_auth
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
        
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
        
    
    pagination = db.getImagesWithPagination(meter_id=meter_id, 
                                            image_requiered=True, 
                                            flag=flag, 
                                            page=page, 
                                            per_page=20,
                                            start_date=start_date,
                                            end_date=end_date)
    
    flags = ["OK", "RNV", "NT", "IV", "DNR", "NED", "D", "PE"]
    
    return render_template('images.html', meter_id=meter_id, pagination=pagination, flag=flag, flags=flags, endpoint='renderImagesWithPagination')


@app.route("/values", methods=['GET'])
@requires_auth
def renderValuesWithPagination():
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
    
    pagination = db.getImagesWithPagination(meter_id=meter_id, image_requiered=False, flag=flag, page=page, per_page=100)
    
    flags = ["OK", "RNV", "NT", "IV", "DNR", "NED", "D", "PE"]
    
    return render_template('values.html', meter_id=meter_id, pagination=pagination, flag=flag, flags=flags, endpoint='renderValuesWithPagination')


@app.route("/knn_data", methods=['GET'])
@requires_auth
def renderKNNData():
    '''
    '''
    meter_id = request.args.get('meter_id')
    knn_data = db.getKNNData(meter_id=meter_id)
    items = dict.fromkeys(range(0, 10))
    
    for i in range(0, 10):
        items[i] = []
    
    for item in knn_data:
        img = cPickle.loads(item.src_image).getPreparedImage()
        try:
            items[item.response].append({'image' : json.dumps(img.tolist()), 
                                         'id': item.id})
        except Exception:
            traceback.print_exc()
        
    return render_template('knn_data.html', meter_id=meter_id, items=items)


@app.route("/meters", methods=('GET', 'POST'))
@requires_auth
def renderMeters():
    '''
    '''
    if app.config["MONGODB_SETTINGS"]['DB'] == '':
        return redirect("/settings", code=302)
    
    return render_template('meters.html', meter=db.getMeters().first())


@app.route("/meter_settings", methods=('GET', 'POST'))
@requires_auth
def renderMeterSettings():
    '''
    '''
    # TODO select meter by id in request
    meter = db.getMeters().first()
    meter_settings = meter.meter_settings
    MSForm = model_form(MeterSettings, Form)
    meter_settings_form = MSForm(request.form, meter_settings)
    
    if meter_settings_form.validate_on_submit():
        meter_settings_form.populate_obj(meter_settings)
        meter_settings.save()
        
    return render_template('meter_settings.html', meter=meter, input_form=meter_settings_form)


@app.route("/meter_image_settings", methods=('GET', 'POST'))
@requires_auth
def renderMeterImageSettings():
    '''
    '''
    # TODO select meter by id in request
    meter = db.getMeters().first()
    
    meter_image_settings = meter.meter_image_settings
    MISForm = model_form(MeterImageSettings, Form)
    meter_image_settings_form = MISForm(request.form, meter_image_settings)

    if meter_image_settings_form.validate_on_submit():
        meter_image_settings_form.populate_obj(meter_image_settings)
        meter_image_settings.save()
        
    return render_template('meter_image_settings.html', meter=meter, input_form=meter_image_settings_form)


@app.route("/knn_settings", methods=('GET', 'POST'))
@requires_auth
def renderKNNSettings():
    '''
    '''
    # TODO select meter by id in request
    meter = db.getMeters().first()
    
    knn_settings = meter.knn_settings
    KNNSForm = model_form(KNNSettings, Form)
    knn_settings_form = KNNSForm(request.form, knn_settings)

    if knn_settings_form.validate_on_submit():
        knn_settings_form.populate_obj(knn_settings)
        knn_settings.save()
        
    return render_template('knn_settings.html', meter=meter, input_form=knn_settings_form)


@app.route("/settings", methods=('GET', 'POST'))
@requires_auth
def renderSettings():
    '''
    '''
#     camera_inputs = db.getCameraInputs()
#     for camera_input in camera_inputs:
    # TODO pass list with all camera inputs to template
        
    return render_template('settings.html')


@app.route("/ci_settings", methods=('GET', 'POST'))
@requires_auth
def renderCiSettings():
    '''
    '''
    # TODO select ci by id in request
    camera_input = db.getCameraInputs().first()
    
    CameraInputForm = model_form(CameraInput, Form)
    camera_input_form = CameraInputForm(request.form, camera_input)
    
    if camera_input_form.validate_on_submit():
        camera_input_form.populate_obj(camera_input)
        camera_input = camera_input.save()
        
        
    return render_template('camera_input_settings.html', input_form=camera_input_form)


@app.route("/db_settings", methods=('GET', 'POST'))
@requires_auth
def renderatDatabaseSettings():
    '''
    '''
    db_name = request.form.get('db_name')
    db_password = request.form.get('db_password') 
    user_password = request.form.get('user_password') 
    
    if db_name is None:
        db_name = app.config["MONGODB_SETTINGS"]['DB']
        db_password = app.config["SECRET_KEY"]
        user_password = get_password()
    
    if db_name != '':
        import flask_server
        flask_server.updateDBConfig(db_name, db_password, user_password)
        #TODO restart server and runner here
        
    return render_template('db_settings.html', db_name=db_name, db_password=db_password, user_password=user_password)


@app.route("/get_meter", methods=['GET'])
@requires_auth
def getMeter():
    '''
    '''
    meter_id = request.args.get('id')
    meter = db.getMeter(meter_id)

    return meter.to_json()
     

@app.route("/get_meters", methods=['GET'])
@requires_auth
def getMeters():
    '''
    '''
    meters = []
    
    for meter in db.getMeters():
        meters.append(json.loads(meter.to_json()))
                 
    return json.dumps(meters)    


@app.route("/get_consumption", methods=['GET'])
@requires_auth
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
@requires_auth
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
@requires_auth
def getImage():
    '''
    '''
    return json.dumps(db.getImage(image_id=request.args.get('id')))


@app.route("/get_images", methods=['GET'])
@requires_auth
def getImages():
    '''
    '''
    # Get data from fields
    meter_id = request.args.get('meter_id')
    flag = request.args.get('flag')     

    return json.dumps(db.getImages(meter_id=meter_id, flag=int(flag)))


@app.route("/delete_meter_value", methods=['GET'])
@requires_auth
def deleteMeterValue():
    '''
    '''
    image_name = request.args.get('image_name')
    value_id = image_name.split('_')[3].split('.')[0]
    
    perm = True if request.args.get('perm') == 'true' else False
    
    if perm:
        Raspimeter.deleteImage(image_name)
        
    deleted_from_db = db.deleteMeterValue(value_id, perm)

    return json.dumps({'deleted_from_db': deleted_from_db})


@app.route("/delete_knn_data", methods=['GET'])
@requires_auth
def deleteKNNData():
    '''
    '''
    meter_id = request.args.get('meter_id')
    ids = json.loads(str(request.args.get('ids')))
    message = "OK"
    
    for id in ids:
        db.deleteKNNData(meter_id, id)

    return json.dumps({'deleted': message})



@app.route("/delete_image", methods=['GET'])
@requires_auth
def deleteImage():
    '''
    '''
    image_name = request.args.get('image_name')
    value_id = image_name.split('_')[3].split('.')[0]
    
    db.deleteImage(value_id)
    Raspimeter.deleteImage(image_name)
    
    return json.dumps({'deleted_from_db': True})


@app.route("/save_digits", methods=['GET'])
@requires_auth
def saveDigits():
    '''
    get_digits?image_name=2016-06-05_21-34-30_5753bea9ca18a204c435d117_57549ae6108d4caa345b1fdb.png
                                                    meter_id                meter_value_id
    '''
    image_name = request.args.get('image_name')
    responses = json.loads(str(request.args.get('responses')))
    train = request.args.get('train')
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
@requires_auth
def getDigits():
    '''
    '''
    image_name = request.args.get('image_name')
    store_recognized_images = True
    
    return json.dumps(Raspimeter.readAndRecognizeImage(db, image_name, store_recognized_images)[3])


@app.route("/recognize_all", methods=['GET'])
@requires_auth
def recognizeAllOnPage():
    '''
    TODO long time request
    '''
    meter_id = request.args.get('meter_id')
    page = int(request.args.get('page'))
    store_recognized_images = True
    success_recogn_counter = Raspimeter.recognizeAllImagesOnPage(db, meter_id, page, store_recognized_images)
    
    return json.dumps({'recognized': success_recogn_counter})


@app.route("/recognize_bulk", methods=['GET'])
@requires_auth
def recognizeBulk():
    '''
    TODO long time request
    '''
    meter_id = request.args.get('meter_id')
    
    return json.dumps({'recognized': "OK"})


@app.route("/restart_server", methods=['GET'])
@requires_auth
def restartServer():
    '''
    '''
    message = "OK"
    
    try:
        call(["sudo", "supervisorctl", "restart", "raspimeter_server"])
    
    except Exception as e:
        message = "ERROR"
        traceback.print_exc()
        
    return json.dumps({'restart_server': message})


@app.route("/controls", methods=['GET'])
@requires_auth
def renderControls():
    '''
    '''
    status_server = "TODO_in_server"
    status_runner = "TODO in server"
    #output = subprocess.check_output(["ping", "-c","2", "-W","2", "1.1.1.1"])
        
    return render_template('controls.html', status_server=status_server, status_runner=status_runner)


@app.route("/restart_runner", methods=['GET'])
@requires_auth
def restartRunner():
    '''
    '''
    message = "OK"
    
    try:
        call(["sudo", "supervisorctl", "restart", "raspimeter_runner"])
    
    except Exception as e:
        message = "ERROR"
        traceback.print_exc()
    
    return json.dumps({'restart_runner': message})
    

@app.route('/js/<path:path>')
@requires_auth
def send_js(path):
    return send_from_directory(os.path.join('js', path).replace('\\','/'))