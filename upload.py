import argparse
import boto
import os
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
import multiprocessing
import os
import shutil
import StringIO
import tempfile
import threading
import time
from gslib.third_party.oauth2_plugin import oauth2_plugin
from gslib.third_party.oauth2_plugin import oauth2_client

import configs

try:
  oauth2_client.token_exchange_lock = multiprocessing.Manager().Lock()
except:
  oauth2_client.token_exchange_lock = threading.Lock()
GOOGLE_STORAGE = 'gs'
#LOCAL_FILE = 'file'
project_id = configs.project_name #'YOUR_DOMAIN:YOUR_PROJECT'
header_values = {"x-goog-project-id": project_id}

def upload_logical_node( logical_id, executable_path, parameter_file_path ):
  executable_file = open( executable_path, 'r' )
  executable_uri = boto.storage_uri( configs.bucket + '/' + logical_id + '/executable', GOOGLE_STORAGE)
  executable_uri.new_key().set_contents_from_file( executable_file )

  parameter_file = open( parameter_file_path, 'r' )
  parameter_file_uri = boto.storage_uri( configs.bucket + '/' + logical_id + '/parameters.default', GOOGLE_STORAGE)
  parameter_file_key = parameter_file_uri.get_key()
