# Set the path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_assets import Bundle, Environment
from flask_server import app 
 
bundles = {
 
    'js': Bundle(
  
        'js/lib/jquery-2.2.4.min.js',
        'js/lib/jquery.tablesorter.min.js',
        'js/lib/jquery-ui.min.js',
        'js/lib/moment-with-locales.min.js',
        'js/lib/jquery.comiseo.daterangepicker.min.js',
        'js/lib/highcharts.js',
        'js/lib/jquery.lazyload.min.js',
        'js/lib/pnglib.js',
        'js/raspimeter.js',
        'js/charts.js',
        output='gen/home.js'),
 
    'css': Bundle(
    
        'css/jquery.comiseo.daterangepicker.css',
        'css/jquery-ui.css',
        'css/styles.css',
        output='gen/home.css'),
 
}
 
assets = Environment(app)
 
assets.register(bundles)