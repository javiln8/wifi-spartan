import requests
import sys

BASE_URL = 'http://127.0.0.1:8081'

def post(msg):
    post = requests.post(BASE_URL + '/api/session', json={'cmd': msg}, auth=('user', 'pass'))
    return post

def get(msg):
    get = requests.get(BASE_URL + '/api/' + msg, auth=('user', 'pass'))
    return get

def delete_events():
    delete = requests.delete(BASE_URL + '/api/events', auth=('user', 'pass'))
    return delete
