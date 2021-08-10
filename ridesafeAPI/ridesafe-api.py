from flask import render_template, flash, redirect, url_for, request, Response, Flask
#from forms import LoginForm, RegistrationForm
from flask_login import logout_user, current_user, login_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.urls import url_parse
from ddtrace import tracer, config, patch_all; patch_all(logging = True)
from datadog import initialize, statsd
import redis, os, json, logging
import ddtrace.profiling.auto
from datetime import time
import requests 
import psycopg2
import ez_pg

app = Flask(__name__)

# ############## Environment Variables #####################

clientToken = os.getenv('DD_CLIENT_TOKEN', '12345')
applicationId = os.getenv('DD_APPLICATION_ID', '12345')
host = os.getenv('DD_AGENT_HOST', '192.168.0.230')
redis_port = os.getenv('REDIS_PORT', '6379')
ridesafe_api_port = os.getenv('RIDESAFE_API_PORT', '8080')

# ############## Environment Variables #####################


try:
    database = ez_pg.dbActions('postgresdb', 'postgresadmin', password="admin123", host="rs-postgres.default.svc.cluster.local", port="5432")

        
except Exception as e:
    print("can't connect. Invalid dbname, user or password?")
    print(e)


############# DogStatsD & Tracer Configuration ###############

options = {
    'statsd_host': host,
    'statsd_port':8125
}
initialize(**options)

# Global config - Tracer
config.trace_headers([
    'user-agent', 
    'transfer-encoding', 
])

############## Log Configuration ########################


FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')

werkzeug = logging.getLogger('werkzeug')
if len(werkzeug.handlers) == 1:
    formatter = logging.Formatter(FORMAT)
    werkzeug.handlers[0].setFormatter(formatter)

logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.level = logging.INFO



############### Rate Limiting Config #######################

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["3600 per hour"]
)


##############  Track the hackers! (404 error handling) ######################

@tracer.wrap()
@app.errorhandler(404)
def not_found(e): 
    root_span = tracer.current_root_span()
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    root_span.set_tag("originating_ip", ip)
    root_span.set_tag('http.status_code', '404')
    return render_template('404.html', applicationId = applicationId, clientToken = clientToken)


#################### Ui Endpoints ##########################

# Index page
@tracer.wrap()
@app.route('/', methods = ['GET'])
def index():
   
    try:
        database.select('crash_data')

    except Exception as e:
        log.info("Can't connect to the Database")
        log.info(e)
    log.info(dict(request.headers))
    return render_template('index.html', title = 'Home', applicationId = applicationId, clientToken = clientToken)

# Gallery
@app.route('/gallery', methods = ['GET'])
@tracer.wrap()
def gallery():
    log.info('Gallery Accessed')
    return render_template('gallery.html', title = 'App Gallery', applicationId = applicationId, clientToken = clientToken)


#File handle
@tracer.wrap()
@app.route("/favicon.ico", methods = ['GET'])
def favicon():
    log.info('/favicon.ico requested')
    return Response(status = 200, mimetype = 'application/json')


# ################## API Endpoints #############################


# Add a crashpoint to the Database - RidesafeMTB Application
# Example Request: curl  -H "Content-Type: application/json" -d '{"username":"john","latitude":"56.66785675","longitude":"65.4344"}' 127.0.0.1:8000/crashPoint/add


@limiter.limit("3600 per minute")
@tracer.wrap()
@app.route('/crash/verify', methods = ['POST'])
def verify_crash_point():
    API_ENDPOINT ='http://ridesafe-learning.default.svc.cluster.local' + ':' + str(ridesafe_api_port) + '/regression/classify'
    incoming = request.get_json()
    g = incoming['g']
    x = incoming['x']
    y = incoming['y']
    z = incoming['z']
   
    # data to be sent to ridesafe-learning
    data = {'g': g, 
            'x': x, 
            'y': y, 
            'z': z } 
    # sending post request and saving response as response object 
    r = requests.post(url = API_ENDPOINT, data = data)   
    # extracting response text  
    reply = r.text 
    status = 'false'
    if(float(reply) > 0.7):
        status = 'true'
    return Response("{'crash status':" + status + "}", status = 200, mimetype = 'application/json')

# Example Request: curl  -H "Content-Type: application/json" -d '{"g": 45,"x": 0.8676,"y":0.7676,"z": 0.77676767}' localhost:30000/crash/verify



if __name__ == '__main__':
    app.run()