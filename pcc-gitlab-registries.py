# -*- coding: utf-8 -*-

import sys
import os.path
import json
import getpass
import argparse
import requests
from dotenv import dotenv_values


__author__ = 'Victor Knell'
__copyright__ = 'Copyright 2021, Palo Alto Networks'
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = 'Victor Knell'
__email__ = 'vknell@paloaltonetworks.com'
__status__ = 'Dev'


parser = argparse.ArgumentParser(prog='pcc-gitlab-registries',
                                 usage='%(prog)s [-lrjcsv] ',
                                 description='Add your Gitlab Registry in Prisma Cloud Compute - \
                                 .env file can be used (COMPUTE_API_ENDPOINT, ACCESS_KEY, SECRET_KEY) - \
                                 Populate the gitlab.json file with the JSON output from Gitlab\
                                 Example: curl --header "PRIVATE-TOKEN: <your_access_token>" "https://gitlab.example.com/api/v4/projects/5/registry/repositories" - \
                                 Use -l to return the list of credentials and collections\
                                 Example: python pcc-gitlab-registries.py -l - \
                                 Use -c and -s to add your selected credentials and collection\
                                 Example: python pcc-gitlab-registries.py -c CRED -s SCOPE'
                                 )
parser.version = __version__
parser.add_argument('-l', '--list',
                    # metavar='',
                    default=False,
                    action='store_true',
                    help='List the credentials and collections that can be used')
parser.add_argument('-r', '--registry',
                    metavar='',
                    default='registry.gitlab.com',
                    help='Enter the registry address, default is registry.gitlab.com')
parser.add_argument('-j', '--json',
                    metavar='',
                    default='gitlab.json',
                    help='Path of the json file containing all Gitlab repositories, default gitlab.json')
parser.add_argument('-c', '--credentials',
                    metavar='',
                    help='Credentials to be provided for this registry')
parser.add_argument('-s', '--scope',
                    metavar='',
                    default='All',
                    help='Select the scope/collection')
parser.add_argument('-v', '--version', action='version')
args = parser.parse_args()


# get a key securely in the terminal
def get_key(string):
    if sys.stdin.isatty():
        secret = getpass.getpass(str(string))
    else:
        secret = sys.stdin.readline().rstrip()
    return secret


def check_env():
    if os.path.isfile('.env'):
        return True
    return False


def get_env_variables():
    # check if an .env file exists
    if check_env():
        credentials = dotenv_values(".env")
        if "COMPUTE_API_ENDPOINT" in credentials:
            url = credentials['COMPUTE_API_ENDPOINT']
        else:
            url = input("Enter the compute path to the Console (Compute>System>Utilities): ")
        if "ACCESS_KEY" in credentials:
            access_key = credentials['ACCESS_KEY']
        else:
            access_key = get_key("Enter your Access Key: ")
        if "SECRET_KEY" in credentials:
            secret_key = credentials['SECRET_KEY']
        else:
            secret_key = get_key("Enter your Secret Key: ")
    else:
        # prompt for the access & secret keys
        url = input("Enter the compute path to the Console (Compute>System>Utilities): ")
        access_key = get_key("Enter your Access Key: ")
        secret_key = get_key("Enter your Secret Key: ")
    return url, access_key, secret_key


def check_path():
    if not (os.path.isfile(args.json) and args.json.startswith("/")):
        args.json = os.getcwd() + '/' + args.json
    if not os.path.isfile(args.json):
        print('The path specified for the json file does not exist')
        sys.exit()


def auth_get_token(url, user, password):
    """
    Method to get the JWT after login using the Access Key and the Secret Key
    Returns token
    """
    r_url = "https://{}/api/v1/authenticate".format(url)
    r_headers = {
        'content-Type': 'application/json; charset=UTF-8',
    }
    r_data = {
        'username': '{}'.format(user),
        'password': '{}'.format(password),
    }
    r = requests.post(r_url, headers=r_headers, data=json.dumps(r_data))
    token = r.json().get('token')
    return token


def api_get(url, endpoint, token, data=""):
    """
    Method to query the Prisma Cloud CSPM API using the GET method
    Returns requests object
    """
    r_url = "https://{}/api/v1/{}".format(url, endpoint)
    r_headers = {
        'content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Authorization': 'Bearer {}'.format(token),
    }
    r = requests.get(r_url, headers=r_headers, data=json.dumps(data))
    return r


def api_post(url, endpoint, token, data=""):
    """
    Method to query the Prisma Cloud CSPM API using the POST method
    Returns requests object
    """
    r_url = "https://{}/api/v1/{}".format(url, endpoint)
    r_headers = {
        'content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer {}'.format(token),
    }
    r = requests.post(r_url, headers=r_headers, data=json.dumps(data))
    return r


def api_put(url, endpoint, token, data=""):
    """
    Method to query the Prisma Cloud CSPM API using the PUT method
    Returns requests object
    """
    r_url = "https://{}/api/v1/{}".format(url, endpoint)
    r_headers = {
        'content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer {}'.format(token),
    }
    r = requests.put(r_url, headers=r_headers, data=json.dumps(data))
    return r


def api_delete(url, endpoint, token, data=""):
    """
    Method to query the Prisma Cloud CSPM API using the DELETE method
    Returns requests object
    """
    r_url = "https://{}/api/v1/{}".format(url, endpoint)
    r_headers = {
        'content-Type': 'application/json; charset=UTF-8',
        'Authorization': 'Bearer {}'.format(token),
    }
    r = requests.delete(r_url, headers=r_headers, data=json.dumps(data))
    return r


def get_credentials(url, token):
    """
    Get the credentials list
    Returns requests object
    """
    r_endpoint = "credentials"
    r = api_get(url, r_endpoint, token)
    return r


def get_collections(url, token):
    """
    Get the collections list
    Returns requests object
    """
    r_endpoint = "collections"
    r = api_get(url, r_endpoint, token)
    return r


def set_registry(url, token, registry, repository, credentials, collection):
    r_endpoint = "settings/registry"
    r_data = {
        "version": "2",
        "registry": registry,
        "repository": repository,
        "tag": "",
        "os": "linux",
        "cap": 5,
        "hostname": "",
        "scanners": 2,
        "collections": [collection]
    }
    r = api_post(url, r_endpoint, token, r_data)
    return r


def list_basic_credentials(url, token):
    r = get_credentials(url, token)
    for i in r.json():
        if not i.get('external'):
            print('{}'.format(i['_id']))


def list_collections(url, token):
    r = get_collections(url, token)
    for i in r.json():
        if i.get('name'):
            print('{}'.format(i['name']))


def read_repository_list():
    repo_list = []
    with open(args.json, 'r') as f:
        repositories = json.load(f)
        for i in repositories:
            if i.get('path'):
                repo_list.append(i['path'])
    return repo_list


def add_repositories(url, token, registry, credentials, collection):
    for i in read_repository_list():
        set_registry(url, token, registry, i, credentials, collection)


if __name__ == "__main__":
    # check json file path is valid
    check_path()
    registry = args.registry
    credentials = args.credentials
    collection = args.scope
    # get Console path, Access Key, Secret Key
    url, access_key, secret_key = get_env_variables()
    # login and get token
    token = auth_get_token(url, access_key, secret_key)
    if args.list:
        print('Credentials')
        list_basic_credentials(url, token)
        print('')
        print('Collections/Scope')
        list_collections(url, token)
        sys.exit()
    add_repositories(url, token, registry, credentials, collection)


