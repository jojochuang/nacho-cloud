# A python script to terminate a running logical node in Google Compute Engine, and download logs
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
#import cloudstorage as gcs

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

parser.add_argument("id", help="id of the logical node")

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
  scope=[
      'https://www.googleapis.com/auth/compute',
      'https://www.googleapis.com/auth/compute.readonly',
      'https://www.googleapis.com/auth/devstorage.full_control',
      'https://www.googleapis.com/auth/devstorage.read_only',
      'https://www.googleapis.com/auth/devstorage.read_write',
    ],
    message=tools.message_if_missing(CLIENT_SECRETS))

try:
  oauth2_client.token_exchange_lock = multiprocessing.Manager().Lock()
except:
  oauth2_client.token_exchange_lock = threading.Lock()

GOOGLE_STORAGE = 'gs'
LOCAL_FILE = 'file'
project_id = configs.project_name #'YOUR_DOMAIN:YOUR_PROJECT'
header_values = {"x-goog-project-id": project_id}

def get_instance_names( logical_id ):
  # TODO: use Google storage to get the corresponding instance ids
  # TODO: Google offers multiple storages: app engine, google cloud sql, google cloud storage
  instance_names = []
  #instances = gcs_file = gcs.open('weichiu/' + logical_id + "_instances" ).read()
  uri = boto.storage_uri( configs.bucket + '/' + logical_id + '/instances.txt', GOOGLE_STORAGE)
  key = uri.get_key()
  instances = key.get_contents_as_string()
  print instances
  instance_names = instances.split('\n')
  return instance_names


def  remove_metadata( logical_id ):
  uri = boto.storage_uri( configs.bucket + '/' + logical_id + '/instances.txt', GOOGLE_STORAGE)
  uri.delete()

  uri = boto.storage_uri( configs.bucket + '/' + logical_id + '/executable', GOOGLE_STORAGE)
  uri.delete()

  uri = boto.storage_uri( configs.bucket + '/' + logical_id + '/param.default', GOOGLE_STORAGE)
  uri.delete()

def read_key():
  uri = boto.storage_uri('weichiu/foo.txt', GOOGLE_STORAGE)
  key = uri.get_key()

  print key.get_contents_as_string()
  #print key.metadata
  #print json.dumps( key )

def list_buckets():
  uri = boto.storage_uri('', GOOGLE_STORAGE)
  # If the default project is defined, call get_all_buckets() without arguments.
  for bucket in uri.get_all_buckets(headers=header_values):
    print bucket.name

def create_buckets():
  # URI scheme for Google Cloud Storage.
  # URI scheme for accessing local files.
  now = time.time()
  CATS_BUCKET = 'cats-%d' % now
  DOGS_BUCKET = 'dogs-%d' % now

  # Your project ID can be found at https://console.developers.google.com/
  # If there is no domain for your project, then project_id = 'YOUR_PROJECT'

  for name in (CATS_BUCKET, DOGS_BUCKET):
    # Instantiate a BucketStorageUri object.
    uri = boto.storage_uri(name, GOOGLE_STORAGE)
    # Try to create the bucket.
    try:
      # If the default project is defined,
      # you do not need the headers.
      # Just call: uri.create_bucket()
      uri.create_bucket(headers=header_values)

      print 'Successfully created bucket "%s"' % name
    except boto.exception.StorageCreateError, e:
      print 'Failed to create bucket:', e

def main(argv):
  flags = parser.parse_args(argv[1:])
  # reads the logical node id, and find out the associated instances.

  storage = file.Storage('sample.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(FLOW, storage, flags)

  http = httplib2.Http()
  http = credentials.authorize(http)


  # TODO: transfer logs from nodes to cloud storage

  instance_names = get_instance_names( flags.id )

  service = discovery.build('compute', 'v1', http=http)
  print "total number of instances associated with the logical id is " + len( instance_names )
  try:
    for instance_name in instance_names:
      print "deleting instance '" + instance_name + "'"
      request = service.instances().delete(project = configs.project_name, zone= configs.zone, instance= instance_name )
      response = request.execute()
      #req = service.instances().list(project= configs.project_name )


  except client.AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")

  remove_metadata( flags.id )

if __name__ == '__main__':
  #read_key()
  #list_buckets()
  #create_buckets()
  main(sys.argv)
