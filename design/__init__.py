#imports

import os
import pymongo
from pymongo import Connection
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask.ext.wtf import Form, TextField, TextAreaField, \
    PasswordField, SubmitField, Required, ValidationError
from flask.ext.bcrypt import Bcrypt, generate_password_hash, \
	check_password_hash



path = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')
upload_path = os.path.join('.', os.path.dirname(__file__), 'static/img/uploads/')

if not os.path.isdir(upload_path):
	os.makedirs(upload_path)

#define app
app = Flask(__name__)

#define bcrypt
bcrypt = Bcrypt(app)

#define the configuration
app.config.from_pyfile('config.cfg')

app.config['SIJAX_STATIC_PATH'] = path
app.config['SIJAX_JSON_URI'] = '/static/js/sijax/json2.js'
app.config['UPLOADS_FOLDER'] = upload_path

#pymongo config
#conn = Connection(app.config['MONGO_URI'])
conn = Connection('localhost',45000)
#db = conn[app.config['MONGO_DB']]
db = conn['design_db']
users = db['accesslist']
images = db['img']
researchsessions = db['allsessions']
uisettings = db['uisettings']
reports = db['reports']
groups = db['imagegroup']

#imports forms models and views
import design.views