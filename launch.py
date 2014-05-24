# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command-line skeleton application for Compute Engine API.
Usage:
  $ python sample.py

You can also get help on all the command-line flags the program understands
by running:

  $ python sample.py --help

"""

import argparse
import httplib2
import os
import sys

import boto

from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools

import json

import configs
import upload

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])


# CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret. You can see the Client ID
# and Client secret on the APIs page in the Cloud Console:
# <https://cloud.google.com/console#/project/536582301963/apiui>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

# Set up a Flow object to be used for authentication.
# Add one or more of the following scopes. PLEASE ONLY ADD THE SCOPES YOU
# NEED. For more information on using scopes please see
# <https://developers.google.com/+/best-practices>.
FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
  scope=[
      'https://www.googleapis.com/auth/compute',
      'https://www.googleapis.com/auth/compute.readonly',
      'https://www.googleapis.com/auth/devstorage.full_control',
      'https://www.googleapis.com/auth/devstorage.read_only',
      'https://www.googleapis.com/auth/devstorage.read_write',
    ],
    message=tools.message_if_missing(CLIENT_SECRETS))

GOOGLE_STORAGE = 'gs'
project_id = configs.project_name #'YOUR_DOMAIN:YOUR_PROJECT'
header_values = {"x-goog-project-id": project_id}
def create_bucket( bucket ):
  try:
    uri = boto.storage_uri( bucket  , GOOGLE_STORAGE)
    uri.create_bucket(headers=header_values)
  except boto.exception.StorageCreateError, e:
    print 'Failed to create bucket:', e

def store_param_file( bucket, param_file_name ):
  #try:
    param_file = open( param_file_name , 'r' )
    uri = boto.storage_uri( bucket + '/param.default', GOOGLE_STORAGE)
    uri.new_key().set_contents_from_file( param_file )
  #except boto.exception.StorageCreateError, e:
    #print 'Failed to create bucket:', e
def store_executable( bucket, executable_name ):
  #try:
    executable_file = open( executable_name , 'r' )
    uri = boto.storage_uri( bucket + '/executable', GOOGLE_STORAGE)
    uri.new_key().set_contents_from_file( executable_file )
  #except boto.exception.StorageCreateError, e:
    #print 'Failed to create bucket:', e


def store_metadata( logical_id, param_file_name, executable_name ):
  bucket = "nacho" + str(logical_id)
  create_bucket( bucket )
  store_param_file( bucket, param_file_name )
  store_executable( bucket, executable_name )

def start_logical_node( logical_id):
  # If the credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # credentials will get written back to the file.
  storage = file.Storage('sample.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(FLOW, storage)
    #credentials = tools.run_flow(FLOW, storage, flags)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Construct the service object for the interacting with the Compute Engine API.
  service = discovery.build('compute', 'v1', http=http)
  try:
    #print "Success! Now add code here."

    req = service.zones().list(project= configs.project_name )
    rep = req.execute()
    items = rep['items']
    for item in items:
      print item['name'] + "\n"
    #print json.dumps( rep )
    #print service.instances().list(project='Nacho')
    
    # TODO: every time this script is called, 
    # 
    # launches a new logical node. create a logical id
    logical_id = 'test_node'
    # must upload the executable and parameter files into a repository or metadata server
    # (TODO: create an upload.py script )
    upload.upload_logical_node( logical_node, executable_path, parameter_path )
    # supply in the parameter the uri to the executable
    # initially, start an instance as the bootstrapper/ initial leader. ( service.instances().insert() )
    #insert_leader_request = {
    #  'name': 'bootstrapper',
    #}
    #service.instances().insert(project= configs.project_name, zone=configs.zone, insert_leader_request)


    # assigns a metadata key/value pair so that the instance knows it's the bootstrapper
    # assigns a metadata key/value pair for the parameter file
    # assigns a metadata key/value pair to the uri of the executable and download it
    # wait until it is ready and get the ip address
    # (periodically ping using service.instances().get() 
    # start initial peers, set up metadata key/value pair to join the logical node.
    # 
    # TODO: use libcloud to support more cloud infrastructures

    

  except client.AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")

def main(argv):
  # Parse the command-line flags.
  parser.add_argument('-p')
  parser.add_argument('-e')
  flags = parser.parse_args(argv[1:])


  param_file_name = flags.p
  executable_name = flags.e




  logical_id = 1
  store_metadata( logical_id, param_file_name, executable_name )

  #start_logical_node( logical_id)


# For more information on the Compute Engine API you can visit:
#
#   https://developers.google.com/compute/docs/reference/latest/
#
# For more information on the Compute Engine API Python library surface you
# can visit:
#
#   https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/
#
# For information on the Python Client Library visit:
#
#   https://developers.google.com/api-client-library/python/start/get_started
if __name__ == '__main__':
  main(sys.argv)
