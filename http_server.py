#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
from flask import request
from flask import jsonify

import rethinkdb as r

from random import randint
from time import time

import json

app = Flask(__name__)

def md5sum(filename):
    try:
        hash = md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
                hash.update(chunk)
        return hash.hexdigest()
    except:
        return None

@app.route("/", methods=["GET"])
def index():
    return('''
    <html>
        <head>
            <title>Munyal API</title>
        </head>
        <body>
            <h1>Munyal private API</h1>
        </body>
    </html>
    ''')

@app.route("/upload", methods=["POST"])
def upload():
    try:
        r.connect( "localhost", 28015).repl()
        cursor = r.table("changes")
        
        host = request.form.get("host")
        action = request.form.get("action")
        route = request.form.get("route")
        obj = {
            'id' : str(time()).split('.')[0] + str(randint(1, 1000000)),
            'action': action,
            'route': route,
            'host': host
        }
        status = 'ok'
        try:
            cursor.insert(obj).run()
        except:
            status = 'error'
    except:
        status = 'error'
    obj['status'] = status
    return jsonify(obj)
    

if __name__ == '__main__':
    app.run(debug=True)
