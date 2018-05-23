#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hashlib import md5

import os
import json


def md5sum(filename):
    try:
        hash = md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
                hash.update(chunk)
        return hash.hexdigest()
    except:
        return None

def get_json(path):
    out = []
    items = os.listdir(path)
    try:
        for item in items:
            if item[0] != ".":
                item_json = {
                    "name": item
                }
                route = os.path.join(path, item)
                if os.path.isdir(route):
                    item_json["is_file"] = False
                    item_json["content"] = get_json(route)
                elif os.path.isfile(route):
                    item_json["is_file"] = True
                    item_json["size"] = os.path.getsize(route)
                    item_json["last_modified"] = os.path.getmtime(route)
                    item_json["created_at"] = os.path.getctime(route)
                    checksum = md5sum(route)
                    if checksum:
                        item_json["checksum"] = checksum
                    else:
                        item = None
                out.append(item_json)
    except:
        return get_json(path)
    return out

if __name__ == "__main__":
    output = get_json("/media/kirbylife/DATOS/Proyectos/PyCharmProjects/Munyal/folder_test")
    print(json.dumps(output, indent=4))
