# =============================================================================
# STD:
# =============================================================================
import os
import json
from dotenv import load_dotenv
# =============================================================================
# OTHER:
# =============================================================================
import ROOT

from flask import (Flask, request, abort, jsonify, current_app)
from functools import wraps

# =============================================================================
os.environ.setdefault('ENV', 'default')
env_file = os.path.abspath(os.path.join('envs', "%s.env" % os.getenv('ENV')))
print('*' * 80)
print("Read environment from '{}'".format(env_file))
load_dotenv(env_file)

# =============================================================================
# Constants:
# =============================================================================
ROOT_DATA = os.path.abspath(os.getenv(
    'ROOT_DATA',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
))
print("Path to ROOT directory '{}'".format(ROOT_DATA))
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_HOST = os.getenv('FLASK_HOST', None)
KEY_FILES = 'files'
KEY_ITEMS = 'items'
DELIM = ','
DEBUG = False
# =============================================================================
app = Flask("ROOT service")
app.debug = DEBUG

# =============================================================================
# Functions:
# =============================================================================


def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function

# Try to Get the object if fully qualified (i.e. complete path given)
# il fails try a FindObjectAny which find object by name in the 
# list of memory objects of the current directory or its sub-directories. 
# returns the JSON version of the object or None
def process_item(root, item):
    obj = root.Get(item)
    if not obj:
      obj = root.FindObjectAny(item)
    if obj:
        obj_json = json.loads(str(ROOT.TBufferJSON.ConvertToJSON(obj)))
        return obj_json
    return None

# Parse the given directory: "folder" 
# returns a dictionary with:
#   "folders": sorted list of sub-directories Titles
#   "objects": sorted list of objects Names
def process_folder(root, folder):
  if not folder:
    return None
  listd = []
  listl = []
  if root.cd(folder):
    for kname in ROOT.gDirectory.GetListOfKeys():
      if kname.IsFolder():
        listd.append(kname.GetTitle())
      else:
        listl.append(kname.GetName())
  else:
    return None      
  return {"folders": sorted(listd), "objects": sorted(listl)}     


# Process the list of items AND the list of folders for the given filename
# returns a dictionary:
#   "root": the filename processed
#   "items": a dictionary with all the processed items
#   "trees": a dictionary with all the processed folders
def process_file(filename, items, folders):
    filename_abs = os.path.join(ROOT_DATA, filename)
    if os.path.isfile(filename_abs):
        root = ROOT.TFile.Open(filename_abs, "READ")
        if not root:
            return None
        json_items = {}
        for item in items:
            json_item = process_item(root, item)
            if json_item:
                json_items[item] = json_item        
        json_folders = {}
        for folder in folders:
            json_folder = process_folder(root, folder)
            if json_folder:
                json_folders[folder] = json_folder                  
        return {"root": filename, "items": json_items, "trees": json_folders}
    else:
        print("File '%s' does not exists" % filename_abs)
    return None


# =============================================================================
# Routes:
# =============================================================================


@app.route('/')
@jsonp
# args: 
#   files: [REQUIRED] list of root files to be processed
#   items: list of objects that need to be retrieved; first uses the Get function
#          to retrieve it, if fails uses FindObjectAny, if fails again returns None
#   folders: list of directories to be parsed; for each folder returns two lists: 
#           "folders" with the list of the Titles of the sub-directories and 
#           "objects" with the list of the Names of the objects inside the folder. 
# returns "result", a list of dictionaries (one per file) with:
#   "root": the filename processed
#   "items": a dictionary with all the processed items
#   "trees": a dictionary with all the processed folders
def service():
    """ Main service """
    result = []
    # -------------------------------------------------------------------------
    files = request.args.get(KEY_FILES, None)
    items = request.args.get(KEY_ITEMS, '')
    folders = request.args.get(KEY_FOLDERS, '')
    if not files:
        abort(404)

    # -------------------------------------------------------------------------
    for f in files.split(DELIM):
        json_file = process_file(f, items.split(DELIM), folders.split(DELIM))
        if json_file:
            result.append(json_file)

    # -------------------------------------------------------------------------
    return jsonify(result=result)

if __name__ == '__main__':

    app.run(host=FLASK_HOST, port=FLASK_PORT)
