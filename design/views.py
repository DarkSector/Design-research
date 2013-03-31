from __future__ import with_statement

import os
import re
import random
from datetime import date
import pymongo
from pymongo import Connection
from bson.objectid import ObjectId, InvalidId
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from werkzeug import secure_filename
from flask.ext.bcrypt import Bcrypt, generate_password_hash, \
	 check_password_hash
import flask_sijax

from design import app
from design import db
from design import users
from design import images
from design import researchsessions
from design import uisettings
from design import reports
from design import groups


today = date.today()

flask_sijax.Sijax(app)

def allowed_file(filename):
	"""
	This function checks whether the mimetype is allowed or not. We could
	additionally put a check in the form itself
	"""
	return '.' in filename and filename.rsplit('.',1)[1] in \
	 							app.config['ALLOWED_EXTENSIONS']
	
def generate_unique_id(inputname):
	"""
	function simply removes special characters
	converts to lowercase
	removes alphanumerics
	removes double spaces
	hyphenates spaces
	"""
	lowercase = inputname.lower()
	alpharemoved = re.sub(r'[^\w]',' ',lowercase)
	singlewhitespace = alpharemoved.replace("  "," ")
	trailingremoved = singlewhitespace.lstrip().rstrip()
	unique = trailingremoved.replace(" ","-")
	return unique


def get_list_of_uploads():
	"""docstring for get_list_of_uploads"""
	uploadslist = os.listdir(app.config['UPLOADS_FOLDER'])
	return uploadslist

def check_if_images_exist():
	"""
	This function checks if the image name that exists in the Database
	is present in the uploads folder. If it's not, delete the record
	"""
	actualuploads = get_list_of_uploads()
	for selected_image in images.find():
		if not selected_image['name'] in actualuploads:
			images.remove(selected_image)
			
@app.route('/')
def hello():
	"""
	Function handler for /
	The first page is supposed to show you all the researchsessions 
	that are ongoing/active.
	"""
	#retrieve from the db all the researchsessions that are ongoing
	activeresearchsessions = researchsessions.find({'status': 'active'})
	ui = uisettings.find({'name' : 'marketing'})
	return render_template('index.html',\
	 						allresearchsessions=activeresearchsessions, \
	 						urlkey="home",\
							ui=ui)
			
@flask_sijax.route(app,'/panel/create')
def create_session():
	"""
	Create and show the form for initiating researchsessions.
	"""
	
	def create_shandler(obj_response, \
						session_name, \
						session_scale,\
						session_description):
		"""
		Session handler: Session1 of Session creator
		"""
		global new_session
		new_session = {'name':session_name, 'scale': session_scale, \
		 			  'description' : session_description, \
		 			  'year': today.year, 'month' : today.month, \
					  'day' : today.day, 'status': 'inactive', \
					  'unique' : generate_unique_id(session_name) }
		#a new session consisting of session name and information is \
		# created and pushed into the databse
		
		#confirmation = researchsessions.insert(new_session)
		#confirmation is the ObjectId of the document
		
		return obj_response.script("$('#session1sub').hide()"), \
		obj_response.script("$('#session1super').show()"), \
		obj_response.script("$('#session2').show()"), \
		obj_response.script("$('#sessionnamereturn').append('" + \
		session_name +"')")
		#must return created session details as well
		
	def create_shandler2(obj_response,minimum_sets, \
	 					acquire_personal_info, require_authentication, \
	 					authentication_passphrase):
		"""
		This is the second part of the session creation, common 
		attributes like authentication and personal information if 
		required are asked here.
		"""
		
		updated_session = {'personalinfo': acquire_personal_info, \
						  'require_auth': require_authentication, \
						  'auth_passphrase': authentication_passphrase}
		new_session.update(updated_session)
		
		if require_authentication == "yes":
			returnauth = "Closed"
		else:
			returnauth = "Open"
			
		#researchsessions.insert(new_session)
		
		return obj_response.script("$('#session2super').show()"), \
		obj_response.script("$('#session2sub').hide()"), \
		obj_response.script("$('#session3').show()"), \
		obj_response.script("$('#sessiontypereturn').append('" +\
		 					returnauth +"')"),\
		obj_response.script("$('#sessionpassreturn').append('" + \
		 					authentication_passphrase + "')")
		
		
	def create_shandler3(obj_response,groupname):
		"""
		This is the third part of the session creation
		image selection
		"""
		session_group = {'group': groupname}
		new_session.update(session_group)
		researchsessions.insert(new_session)
		return obj_response.script("$('#session3super').show()"),\
		obj_response.script("$('#session3sub').hide()"),\
		obj_response.script("$('#congratulations').show()")
	
	if g.sijax.is_sijax_request:
		g.sijax.register_callback('create_session',create_shandler)
		g.sijax.register_callback('create_session2',create_shandler2)
		g.sijax.register_callback('create_session3',create_shandler3)
		return g.sijax.process_request()
	uploaded = images.find()
	allgroups = groups.find()
	return render_template('create_session.html',\
							create_session=True, \
							uploaded=uploaded,\
							allgroups=allgroups)
	
@flask_sijax.route(app,'/panel')
def panel():
	"""
	Panel is where the heart is
	1. It gives you list of all existing researchsessions
	2. It gives you list of all the reports generated
	3. It gives you list of all time images already uploaded
	4. It gives you way to manage user.
	5. It gives you UI settings options
	"""
	#all researchsessions that are in the db are kept here.
	allresearchsessions = researchsessions.find()
	settings = uisettings.find()
	
	def activation_handler(obj_response,session_unique):
		"""
		This function will activate the session
		"""
		fetch_session = researchsessions.find_one({'unique':session_unique})
		fetch_session['status'] = 'active'
		researchsessions.save(fetch_session)
		return obj_response.script("location.reload();")
	
	def deactivation_handler(obj_response,session_unique):
		"""
		Function to deactivate the session
		"""
		fetch_session = researchsessions.find_one({'unique':session_unique})
		fetch_session['status'] = 'inactive'
		researchsessions.save(fetch_session)
		return obj_response.script("location.reload();")
		
	def delete_handler(obj_response, session_unique):
		"""
		Function to delete the session
		"""
		fetch_session = researchsessions.find_one({'unique':session_unique})
		researchsessions.remove(fetch_session)
		return obj_response.script("location.reload();")
		
	def delete_image_handler(obj_response, image_id):
		"""
		This function deletes the image
		"""
		#fetch_image = images.find_one({'name': image_name})
		images.remove(ObjectId(image_id))
		imagediv = "image"+ str(image_id)
		return obj_response.script("$('#"+imagediv+"').remove()")
		
	def create_group_handler(obj_response, groupname):
		"""
		This function creates a group and adds it to the database
		"""
		groups.insert({'name': groupname})
		print groupname
		return obj_response.script('$("#groupname").append("<option value='+ groupname + '>' + groupname + '</option>")'),\
		obj_response.script('$("#newgroupform").reset()')
		
	def delete_group_handler(obj_response, groupname):
		fetch_group = groups.find_one({'name':groupname})
		groupid = fetch_group['_id']
		groups.remove(fetch_group)
		return obj_response.script("$('#group"+str(groupid)+"').remove()")
		
		
	def add_to_group_handler(obj_response, imageid, groupname):
		"""
		Images will have an attribute by the name of groups in which all
		the names of the groups will be added
		"""
		fetch_image = images.find_one(ObjectId(imageid))
		group_list = fetch_image['groups']
		group_list.append(groupname)
		fetch_image['groups'] = group_list
		images.save(fetch_image)
		return obj_response
	
	if g.sijax.is_sijax_request:
		g.sijax.register_callback('activate_session',activation_handler)
		g.sijax.register_callback('deactivate_session',\
			deactivation_handler)
		g.sijax.register_callback('delete_session', delete_handler)
		g.sijax.register_callback('delete_image', delete_image_handler)
		g.sijax.register_callback('create_group', create_group_handler)
		g.sijax.register_callback('delete_group', delete_group_handler)
		g.sijax.register_callback('add_to_group', add_to_group_handler)
		return g.sijax.process_request()
	
	uploads = images.find()
	allgroups = groups.find()
	return render_template('panel.html',\
							allsessions=allresearchsessions,\
							urlkey="panel",\
							allsettings=settings,\
							allimages=uploads,\
							allgroups=allgroups)

@app.route('/about')
def about():
	"""
	Tells the user more about the DRT
	"""
	return render_template('about.html')

@app.route('/upload', methods=["GET","POST"])
def upload_images():
	"""
	Function that handles all the uplaods
	Once the upload is done, all the files are kept in the static folder
	The names of all the images are stored in the db.
	"""
	check_if_images_exist()
	if request.method == "POST":
		image_group = []
		filename_values = []
		for file in request.files.getlist('file'):
			if file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				#filename_values.append(filename)				
				back = file.save(os.path.join\
					(app.config['UPLOADS_FOLDER'], filename))
				if back:
					break
				
				images.insert({'name' : filename, 'groups': image_group})						
	uploaded = images.find()
	return render_template('upload.html', \
							urlkey="upload", \
	 						uploaded=uploaded)
	
#@flask_sijax.route(app,'/edit/session/<session_id>')
def edit_session(session_id):
	"""
	This function edits the premade sessions
	"""
	if not researchsessions.find_one({'unique': session_id}):
		abort(404)
	else:
		pass
	pass
	return render_template('edit.html')
	
@flask_sijax.route(app,'/session/<session_id>')
def get_session(session_id):
	"""
	Session rendering function
	This function renders a session. The session id is the unique name
	of the session
	"""
	
	if not researchsessions.find_one({'unique': session_id }):
		abort(404)
	
	
	def step1_handler(obj_response,\
					  similar_array,\
					  similar_reason,\
				      different_array,\
				      different_reason):
		"""
		step1_handler takes values similar_array and different_array and
		processes them
		"""
		return obj_response.alert("request receieved")
	
	if g.sijax.is_sijax_request:
		g.sijax.register_callback('step1_parse',step1_handler)
		return g.sijax.process_request()
	
	
	allimages = images.find()
	fetched = researchsessions.find_one({'unique':session_id})
	selected = images.find({'groups': fetched['group']})
	selected = random.sample(list(selected), 3)
	
	return render_template('render_session.html', allimages=selected)

@app.errorhandler(404)
def page_not_found(e):
	"""
	Custom error handling for 404
	"""
	return render_template('404.html'), 404
	
@app.route('/login', methods=["GET","POST"])
def login():
	"""
	Login handler
	"""
	return redirect(url_for('hello'))

@app.route('/logout')
def logout():
	"""
	logout handler
	"""
	pass