from flask.ext.wtf import Form
from wtforms import FieldList, FormField, StringField, BooleanField
from wtforms.validators import DataRequired
import wtforms.validators as validators

# 
# class AppSettingsForm(Form):
#     pass

class MeterSettingsForm(Form):
#     meter_settings = 
    pass

class MeterImageSettingsForm(Form):
    pass


class KNNSettingsForm(Form):
    pass


class MeterAllSettingsForm(Form):
    meter_settings = FormField(MeterSettingsForm)
    meter_image_settings = FormField(MeterImageSettingsForm)
    knn_settings = FormField(KNNSettingsForm)


class MetersSettingsForm(Form):
    meters = FieldList(FormField(MeterAllSettingsForm), [validators.required()])
    
    