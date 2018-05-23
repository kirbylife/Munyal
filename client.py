#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from compare_json import compare_json
from dir_to_json import get_json

from copy import deepcopy
from time import sleep
from requests import post
from shutil import rmtree
from threading import Thread
from tcping import Ping

from tkinter import Tk
from tkinter import StringVar
from tkinter import Entry
from tkinter import Button
from tkinter import Label

import rethinkdb as r

import os
import socket
import json
import pathlib
from random import randint
import sys
import ftplib

#ORIGINAL = "/home/kirbylife/Proyectos/munyal_test/another"
ORIGINAL = "/home/kirbylife/Proyectos/munyal_test/"
IP = "localhost"
USERNAME = "munyal"
PASSWORD = "123"
HOSTNAME = socket.gethostname() + str(randint(1, 100000000))
SKIP_UPLOAD = []
FLAG_DOWNLOAD = False
pending_routes = []

def check_network(port):
    ping = Ping(IP, port, 20)
    ping.ping(1)
    print(SKIP_UPLOAD)
    return ping.result.rows[0].successed == 1

def watch_dir():
    global pending_routes
    folder = os.path.join(os.getenv("HOME"), ".munyal")
    if not os.path.exists(folder):
        pathlib.Path(folder).mkdir(parents=True)
        
    actual_file = os.path.join(folder, "actual.json")
    if not os.path.exists(actual_file):
        with open(actual_file, "w") as f:
            f.write(json.dumps([]))
    pending_file = os.path.join(folder, "pending_routes.json")
    if not os.path.exists(pending_file):
        with open(pending_file, "w") as f:
            f.write(json.dumps([]))
            
    with open(actual_file, "r") as f:
        actual = json.loads(f.read())
    actual = get_json(ORIGINAL)
    new = deepcopy(actual)
    with open(pending_file, "r") as f:
        pending_routes = json.loads(f.read())
    new = get_json(ORIGINAL)
    while True:
        sleep(0.2)
        while True:
            try:
                jsons = compare_json(deepcopy(actual), deepcopy(new))
            except:
                new = get_json(ORIGINAL)
            else:
                break
        changes = get_changes(jsons)
        
        pending_routes = pending_routes + changes
        with open(pending_file, "w") as f:
            f.write(json.dumps(pending_routes, indent=4))
        
        actual = deepcopy(new)
        with open(actual_file, "w") as f:
            f.write(json.dumps(actual, indent=4))
        while True:
            try:
                new = get_json(ORIGINAL)
            except:
                pass
            else:
                break

def need_deleted(items, route):
    out = []
    for item in items:
        if item.get("is_file"):
            out.append({"action": "delete", "route": os.path.join(route, item.get('name'))})
        else:
            if item.get('content'):
                out = out + need_deleted(item.get("content"), os.path.join(route, item.get('name')))
            else:
                out.append({"action": "delete_folder", "route": os.path.join(route, item.get('name'))})
    return out

def need_added(items, route):
    out = []
    for item in items:
        if item.get("is_file"):
            out.append({"action": "add", "route": os.path.join(route, item.get('name'))})
        else:
            if item.get('content'):
                out = out + need_added(item.get("content"), os.path.join(route, item.get('name')))
            else:
                out.append({"action": "add_folder", "route": os.path.join(route, item.get('name'))})
    return out

def get_changes(jsons, route=''):
    delete, add = jsons
    out = need_deleted(delete, route) + need_added(add, route)
    return out

def _is_ftp_dir(ftp_handle, name):
    original_cwd = ftp_handle.pwd()
    try:
        ftp_handle.cwd(name)
        ftp_handle.cwd(original_cwd)
        return True
    except:
        return False

def _make_parent_dir(fpath):
    #dirname = os.path.dirname(fpath)
    dirname = os.path.join(ORIGINAL, fpath)
    while not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
            print("created {0}".format(dirname))
        except:
            _make_parent_dir(dirname)

def _download_ftp_file(ftp_handle, name, dest, overwrite):
    if not os.path.exists(dest) or overwrite is True:
        try:
            with open(dest, 'wb') as f:
                ftp_handle.retrbinary("RETR {0}".format(name), f.write)
            print("downloaded: {0}".format(dest))
        except FileNotFoundError:
            print("FAILED: {0}".format(dest))
    else:
        print("already exists: {0}".format(dest))

def _mirror_ftp_dir(ftp_handle, name, overwrite):
    for item in ftp_handle.nlst(name):
        SKIP_UPLOAD.append(item)
        if _is_ftp_dir(ftp_handle, item):
            _make_parent_dir(item.lstrip("/"))
            _mirror_ftp_dir(ftp_handle, os.path.join(name, item), overwrite)
        else:
            _download_ftp_file(ftp_handle, item, os.path.join(ORIGINAL, item), overwrite)

def download_ftp_tree(overwrite=False):
    FLAG_DOWNLOAD = True
    ftp_handle = ftplib.FTP(IP, USERNAME, PASSWORD)
    path = ""
    original_directory = os.getcwd()
    os.chdir(ORIGINAL)
    _mirror_ftp_dir(ftp_handle, path, overwrite)
    os.chdir(original_directory)
    ftp_handle.close()
    FLAG_DOWNLOAD = False

def upload(*args):
    global SKIP_UPLOAD
    global pending_routes
    print("Modulo de subida listo")
    while True:
        sleep(0.1)
        if check_network('21') and pending_routes:
            change = pending_routes.pop(0)
            while FLAG_DOWNLOAD:
                print("Wait")
            if change['route'] not in SKIP_UPLOAD:
                ftp = ftplib.FTP(IP, USERNAME, PASSWORD)
                route = os.path.join(ORIGINAL, change['route'])
                success = False
                while not success:
                    try:
                        if change['action'] == 'add':
                            print("Agregar archivo")
                            with open(route, "rb") as f:
                                ftp.storbinary("STOR /" + change['route'], f)
                        elif change['action'] == 'add_folder':
                            print("Agregar carpeta")
                            ftp.mkd(change['route'])
                        elif change['action'] == 'delete':
                            print("Borrar archivo")
                            ftp.delete(change['route'])
                        elif change['action'] == 'delete_folder':
                            print("Borrar carpeta")
                            ftp.rmd(change['route'])
                        else:
                            print("Unexpected action")
                    except:
                        print("Error uploading\n")
                    r = post("http://"+IP+':5000/upload', data={
                            'host': HOSTNAME,
                            'action': change['action'],
                            'route': change['route']
                        }
                    )
                    r = json.loads(r.text)
                    print(json.dumps(r, indent=4))
                    success = r['status'] == 'ok'
                ftp.close()
            else:
                SKIP_UPLOAD.pop()
    return 0

def download(*args):
    global SKIP_UPLOAD
    while True:
        sleep(1)
        if check_network(28015) and check_network(21):
            try:
                download_ftp_tree(overwrite=False)
                
                print("Modulo de descarga listo")
                print("Carpeta " + ORIGINAL)
                r.connect(IP, 28015).repl()
                cursor = r.table("changes").changes().run()
                for document in cursor:
                    change = document['new_val']
                    #print(change)
                    if change['host'] != HOSTNAME:
                        FLAG_DOWNLOAD = True
                        route = os.path.join(ORIGINAL, change['route'])
                        SKIP_UPLOAD.append(change['route'])
                        try:
                            if change['action'] == 'add':
                                print("Agregar archivo")
                                ftp = ftplib.FTP(IP, USERNAME, PASSWORD)
                                with open(route, "wb") as f:
                                    ftp.retrbinary("RETR /" + change['route'], f.write)
                                ftp.close()
                            elif change['action'] == 'add_folder':
                                print("Agregar carpeta")
                                pathlib.Path(route).mkdir(parents=True)
                            elif change['action'] == 'delete':
                                print("Borrar archivo")
                                pathlib.Path(route).unlink()
                            elif change['action'] == 'delete_folder':
                                print("Borrar carpeta")
                                rmtree(route)
                            else:
                                print("Unexpected action")
                        except OSError as e:
                            print("Error en el sistema operativo")
                        except:
                            print("Error en el servidor FTP")
                        FLAG_DOWNLOAD = False
            except rethinkdb.errors.ReqlDriverError as e:
                print("Conection refused with rethinkdb")
    return 0

def run_client(window, password, username, host, folder):
    global PASSWORD
    global IP
    global USERNAME
    global ORIGINAL
    
    PASSWORD = password.get()
    USERNAME = username.get()
    IP = host.get()
    ORIGINAL = folder.get()
    
    if not os.path.exists(ORIGINAL):
        pathlib.Path(ORIGINAL).mkdir(parents=True)
    
    download_thread = Thread(target=download, args=[window])
    download_thread.setDaemon(True)
    download_thread.start()
    
    upload_thread = Thread(target=upload, args=[window])
    upload_thread.setDaemon(True)
    upload_thread.start()
    
    watch_dir_thread = Thread(target=watch_dir)
    watch_dir_thread.setDaemon(True)
    watch_dir_thread.start()
    
def main(args):
    root = Tk()
    root.geometry("200x300")
    root.title("MUNYAL")
    
    host = StringVar()
    host.set("localhost")
    host_field = Entry(root, textvariable=host)
    
    user = StringVar()
    user.set("munyal")
    user_field = Entry(root, textvariable=user)
    
    passwd = StringVar()
    passwd.set("123")
    passwd_field = Entry(root, textvariable=passwd, show="*")
    
    folder = StringVar()
    folder.set(os.path.join(os.getenv("HOME"), "Munyal"))
    folder_field = Entry(root, textvariable=folder)
    
    connect = Button(root, text="Conectar", command = lambda: run_client(root, passwd, user, host, folder))
    
    Label(root, text="MUNYAL").pack()
    Label(root, text="").pack()
    Label(root, text="Ruta del servidor").pack()
    host_field.pack()
    Label(root, text="").pack()
    Label(root, text="Nombre de usuario").pack()
    user_field.pack()
    Label(root, text="").pack()
    Label(root, text="Contraseña").pack()
    passwd_field.pack()
    Label(root, text="").pack()
    Label(root, text="Carpeta a sincronizar").pack()
    folder_field.pack()
    Label(root, text="").pack()
    connect.pack()
    
    root.mainloop()
    
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
