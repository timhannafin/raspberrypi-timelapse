from TimelapseCamera import TimelapseCamera
from flask import Flask, render_template, send_file, request, g, jsonify
import sqlite3
import os
import datetime
import time
import glob
import subprocess

DATABASE = "/home/pi/timelapse.db"
camera = TimelapseCamera()
camera.resolution = (512, 368)

render_process = []

app = Flask(__name__)


def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(DATABASE)
	return db

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

def write_db(query, args=()):
	get_db().execute(query, args)
	get_db().commit()
	return

def isProjectRunning():
	query = query_db("SELECT rowid FROM projects WHERE status = 'running'")
	if query:
		return True
	else:
		return False

def getProject(id):
	result = None
	query = query_db("SELECT rowid as id,name,capture_interval,frame_count,last_capture,render_start_frame,render_end_frame,codec,status FROM projects WHERE rowid=?",[id],one=True)
	if query:
		result={"id":query[0],"name":query[1],"capture_interval":query[2],"frame_count":query[3],"last_capture":query[4],"render_start_frame":query[5],"render_end_frame":query[6],"codec":query[7],"status":query[8]}
		frames = framesInDir(result["name"])
		result["frame_count"] = frames["frame_count"]
		result["last_capture"] = frames["last_frame_at"]
		result["project_size"] = getDirSize(result["name"])
		return result
	else:
		return result
	
def setActiveProject(id):
	activeProject = getProject(id)
	return
	
def getDirSize(name):
	total_size = 0
	filelist = os.listdir("timelapse_projects/"+name)
	if filelist == []:
		return sizeFormat(0)
	for filename in filelist:
		total_size += os.path.getsize("timelapse_projects/"+name +"/" + filename)
	return sizeFormat(total_size)
	
def sizeFormat(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)
	
def framesInDir(name):
	relativeDir = "timelapse_projects/"+name+"/"
	ret = {}
	ret["frame_count"] = 0;
	ret["last_frame_at"] = "0000-00-00 00:00:00"
	fileList = sorted(os.listdir(relativeDir))
	ret["frame_count"] = len(fileList)
	
	if ret["frame_count"] == 0:
		return ret
	
	lastFrame = fileList[-1]
	ret["last_frame_at"] = datetime.datetime.fromtimestamp(os.path.getmtime(relativeDir + lastFrame)).strftime('%Y-%m-%d %H:%M:%S')
	return ret
	
def setProjectProperty(id,property,value):
	write_db("update projects set " + property + " = ? WHERE rowid=?",[value,id])

def createProject(name):
	write_db("INSERT INTO projects (name) VALUES (?)",[name])
	newProjectId = query_db("SELECT last_insert_rowid() as rowid",one=True)
	newProjectId = newProjectId[0]
	os.mkdir("timelapse_projects/"+name)
	return newProjectId

def deleteFramesInDir(name):
	try:
		files = glob.glob("timelapse_projects/" + name + "/*.jpg")
		for f in files:
			os.remove(f)
	except:
		print "error removing frames"
	return
				
@app.route("/save",methods=["GET"])
def saveProject():
	id = request.args.get('id')
	name = request.args.get('name')
	
	if id == '0':
		id = createProject(name)
		
	setProjectProperty(id,'capture_interval',request.args.get('interval'))
	setProjectProperty(id,'status','created')
	return jsonify(getProject(id))	
	
@app.route("/list-projects")
def listProjects():
	query = query_db("SELECT rowid as id,name,status FROM projects",one=False)
	results = [dict() for x in query]
	i=0
	for row in query:
		results[i]={"id":row[0],"name":row[1],"status":row[2]}
		i+=1
	return jsonify(results)
		
@app.route("/get-project",methods=["GET"])
def getProjectJson():
	id = request.args.get('id')
	project=getProject(id)
	if project:
		return jsonify(project)
	else:
		return jsonify({})
	
@app.route("/start",methods=["GET"])
def start():
	id = request.args.get('id')
	if isProjectRunning():
		return jsonify({"status":"error","message":"Another project is already running"})

	project = getProject(id)
	print project["name"]
	camera.setFrameFilePath("timelapse_projects/" + project["name"])
	camera.setInterval(project["capture_interval"])
	camera.resolution = (1024, 768)
	camera.start()
	setProjectProperty(id,"status","running")
	return jsonify(getProject(id))
	
@app.route("/stop",methods=["GET"])
def stop():
	id = request.args.get('id')
	project = getProject(id)
	camera.stop()
	setProjectProperty(id,"status","stopped")
	return jsonify(getProject(id))		

@app.route("/delete-frames", methods=["GET"])
def deleteFrames():
	id = request.args.get('id')
	project = getProject(id)
	deleteFramesInDir(project["name"])
	return jsonify(getProject(id))
	
@app.route("/delete-project", methods=["GET"])
def deleteProject():
	id = request.args.get('id')
	project = getProject(id)
	deleteFramesInDir(project["name"])
	try:
		os.rmdir("timelapse_projects/" + project["name"])
	except:
		print "Error removing directory"
		
	write_db("DELETE FROM projects WHERE rowid=?", [id])
	return "{}"
	
		
@app.route("/render", methods=["GET"])
def render():
	id = request.args.get('id')
	project = getProject(id)
	setProjectProperty(id,"status","rendering")
	args = ["ffmpeg", "-framerate", "30", "-i", "image%08d.jpg", "../../rendered_videos/"+project["name"]+".mkv"]
	rv = subprocess.Popen(args, cwd="timelapse_projects/" + project["name"]);
	while rv.poll() is None:
		time.sleep(1)
		
	print rv.returncode
	setProjectProperty(id,"status","rendered")
	return jsonify(getProject(id))
	


@app.route("/preview")
def preview():
	if isProjectRunning():
		return
	try:
		camera.capture("preview.jpg")
	except:
		return
	return send_file("preview.jpg", mimetype='image/jpg')


@app.route("/status")
def status():
	return jsonify(getProject(id))

@app.route("/")
def index():
    return send_file("templates/index.html")

