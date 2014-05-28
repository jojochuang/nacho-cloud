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
#def create_bucket( bucket ):
#  try:
#    uri = boto.storage_uri( bucket  , GOOGLE_STORAGE)
#    uri.create_bucket(headers=header_values)
#  except boto.exception.StorageCreateError, e:
#    print 'Failed to create bucket:', e
#    raise

def store_param_file( bucket, param_file_name ):
  try:
    param_file = open( param_file_name , 'r' )
    uri = boto.storage_uri( bucket + '/params.default', GOOGLE_STORAGE)
    uri.new_key().set_contents_from_file( param_file )
  except IOError, e:
      print "can't open the parameter file to read"
  #except boto.exception.StorageCreateError, e:
    #print 'Failed to create bucket:', e
def store_executable( bucket, executable_name ):
  try:
    executable_file = open( executable_name , 'r' )
    uri = boto.storage_uri( bucket + '/executable', GOOGLE_STORAGE)
    uri.new_key().set_contents_from_file( executable_file )
  except IOError, e:
      print "can't open the executable file to read"
  #except boto.exception.StorageCreateError, e:
    #print 'Failed to create bucket:', e


def store_metadata( logical_id, param_file_name, executable_name ):
  print "write metadata"
  try:
    bucket = configs.bucket + "/nacho" + str(logical_id)
    #create_bucket( bucket )
    store_param_file( bucket, param_file_name )
    store_executable( bucket, executable_name )
    # TODO: store the initial logical node composition,
    #   by parsing the parameter file
  except:
    print "failure with creating metadata"
    # TODO: remove metadata
    raise
  print "done"

API_VERSION = 'v1'
GCE_URL = 'https://www.googleapis.com/compute/%s/projects/' % (API_VERSION)
DEFAULT_IMAGE = configs.image
#DEFAULT_ROOT_PD_NAME = 'my-root-pd'
DEFAULT_MACHINE_TYPE = configs.machine
DEFAULT_NETWORK = "default"
def construct_leader_instance_request(logical_id):
  project = configs.project_name
  zone = configs.zone
  name = "nacho-%s-leader" % (logical_id)
  image_url = '%s%s/global/images/%s' % (
         GCE_URL, project, DEFAULT_IMAGE )
  machine_type_url = '%s%s/zones/%s/machineTypes/%s' % (
        GCE_URL, project, zone, DEFAULT_MACHINE_TYPE)
  network_url = '%s%s/global/networks/%s' % (GCE_URL, project, DEFAULT_NETWORK)

  diskName = "nacho-%s-leader-disk" % (logical_id )
  startup_script = "instance-startup.sh"
  request = {
    "disks": [
      {
        "type": "PERSISTENT",
        "boot": True,
        "mode": "READ_WRITE",
        'initializeParams': {
          'diskName': diskName,
          'sourceImage': image_url,
        },
        "autoDelete": True
      }
    ],
    "networkInterfaces": [
      {
        "network": network_url,
        "accessConfigs": [
          {
            "name": "External NAT",
            "type": "ONE_TO_ONE_NAT"
          }
        ]
      }
    ],
    "metadata": {
      "items": [
        {
          "key": "startup-script",
            "value": open( startup_script, "r" ).read()
        },{
          "key": "role",
          "value": "bootstrapper"
        },{
          "key": "logical_id",
          "value": logical_id
        }
      ]
    },
    "tags": {
      "items": []
    },
    "zone": "%s%s/zones/%s" % ( GCE_URL, project, zone),
    "canIpForward": False,
    "scheduling": {
      "automaticRestart": True,
      "onHostMaintenance": "MIGRATE"
    },
    "machineType": machine_type_url,
    "name": name,
    "serviceAccounts": [
      {
        "email": "default",
        "scopes": [
          "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/compute",
          "https://www.googleapis.com/auth/devstorage.full_control"
        ]
      }
    ]
  }
  return request


def construct_peer_instance_request(logical_id, leader_address, nid):
  project = configs.project_name
  zone = configs.zone
  name = "nacho-%s-%d" % (logical_id, nid)
  image_url = '%s%s/global/images/%s' % (
         GCE_URL, project, DEFAULT_IMAGE )
  machine_type_url = '%s%s/zones/%s/machineTypes/%s' % (
        GCE_URL, project, zone, DEFAULT_MACHINE_TYPE)
  network_url = '%s%s/global/networks/%s' % (GCE_URL, project, DEFAULT_NETWORK)

  diskName = "nacho-%s-%d-disk" % (logical_id, nid )
  startup_script = "instance-startup.sh"
  request = {
    "disks": [
      {
        "type": "PERSISTENT",
        "boot": True,
        "mode": "READ_WRITE",
        'initializeParams': {
          'diskName': diskName,
          'sourceImage': image_url,
        },
        "autoDelete": True
      }
    ],
    "networkInterfaces": [
      {
        "network": network_url,
        "accessConfigs": [
          {
            "name": "External NAT",
            "type": "ONE_TO_ONE_NAT"
          }
        ]
      }
    ],
    "metadata": {
      "items": [
        {
          "key": "startup-script",
            "value": open( startup_script, "r" ).read()
        },{
          "key": "role",
          "value": "peer"
        },{
          "key": "logical_id",
          "value": logical_id
        },{
          "key": "bootstrapper",
          "value": leader_address 
        }
      ]
    },
    "tags": {
      "items": []
    },
    "zone": "%s%s/zones/%s" % ( GCE_URL, project, zone),
    "canIpForward": False,
    "scheduling": {
      "automaticRestart": True,
      "onHostMaintenance": "MIGRATE"
    },
    "machineType": machine_type_url,
    "name": name,
    "serviceAccounts": [
      {
        "email": "default",
        "scopes": [
          "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/compute",
          "https://www.googleapis.com/auth/devstorage.full_control"
        ]
      }
    ]
  }
  return request


def start_logical_node( logical_id, nsize):
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
    # supply in the parameter the uri to the executable
    # initially, start an instance as the bootstrapper/ initial leader. ( service.instances().insert() )

    insert_leader_request = construct_leader_instance_request(logical_id)
    request = service.instances().insert(project= configs.project_name, zone=configs.zone, body=insert_leader_request)
    response = request.execute( http = http )
    print "request to create the leader of logical node %s sent. waiting for confirmation" % ( logical_id )
    response = _blocking_call( service, http , response )
    leader_address = get_leader_address( service, http, logical_id  )
    print "done"


    # assigns a metadata key/value pair so that the instance knows it's the bootstrapper
    # assigns a metadata key/value pair for the parameter file
    # assigns a metadata key/value pair to the uri of the executable and download it
    # wait until it is ready and get the ip address
    # start initial peers, set up metadata key/value pair to join the logical node.
    # 
    # TODO: use libcloud to support more cloud infrastructures

    for n in range( 1, int(nsize)+1 ):
      print "start peer node %s" % n
      insert_peer_request = construct_peer_instance_request(logical_id, leader_address, n)
      request = service.instances().insert(project= configs.project_name, zone=configs.zone, body=insert_peer_request)
      response = request.execute( http = http )

      #print "request id %s status %s" % (response['id'], response['status'])
      #print response

      if "error" in response is not None:
        # an error!
        print "error is not None"
        ex = response["error"]
        errors = ex["errors"]
        for e in errors:
          print "error: code %s location %s message %s" % ( e.code, e.location, e.message )

  except client.AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")

def get_leader_address( service, http, logical_id ):
  name = "nacho-%s-leader" % (logical_id)
  request = service.instances().get(project= configs.project_name, zone=configs.zone, instance=name)
  response = request.execute( http = http )
  
  status = response["status"]

  if status != 'RUNNING':
    print "leader is not running. help!" 

  # network interface is an array. get the first interface from the array
  netint = response["networkInterfaces"]
  first_int = netint[0]
  leader_ip = first_int["networkIP"]
  print "leader ip address is %s" % (leader_ip)

  return leader_ip
  

# copied from Google's tutorial: https://developers.google.com/compute/docs/api/python-guide#addinganinstance
def _blocking_call(gce_service, auth_http, response):
  """Blocks until the operation status is done for the given operation."""

  status = response["status"]
  while status != 'DONE' and response:
    operation_id = response['name']

    # Identify if this is a per-zone resource
    if 'zone' in response:
      zone_name = response['zone'].split('/')[-1]
      request = gce_service.zoneOperations().get(
          project=project_id,
          operation=operation_id,
          zone=zone_name)
    else:
      request = gce_service.globalOperations().get(
           project=project_id, operation=operation_id)

    response = request.execute(http=auth_http)
    if response:
      status = response['status']
  return response

def main(argv):
  # Parse the command-line flags.
  parser.add_argument('-p')
  parser.add_argument('-e')
  parser.add_argument('-l')
  parser.add_argument('-n')
  flags = parser.parse_args(argv[1:])

  param_file_name = flags.p
  executable_name = flags.e
  # TODO: use something to store the counter 
  logical_id = flags.l
  nsize = flags.n

  store_metadata( logical_id, param_file_name, executable_name )
  start_logical_node( logical_id, nsize)


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
