#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from dir_to_json import get_json

def compare_json(json1, json2):
    bckup1, bckup2 = json1[:], json2[:]
    items1 = list(enumerate(json1))
    items2 = list(enumerate(json2))
    for i, item1 in items1:
        for j, item2 in items2:
                if item1["name"] == item2["name"]:
                    if item1["is_file"] == True == item2["is_file"]:
                        if item1["checksum"] == item2["checksum"]:
                            json1[i] = None
                            json2[j] = None
                        '''
                        else:
                            json1[i]["tag"] = "update"
                            json2[j] = None
                        '''
                    elif item1["is_file"] == False == item2["is_file"]:
                        new_json1, new_json2 = compare_json(item1["content"], item2["content"])
                        if len(new_json1) == 0:
                            json1[i] = None
                        else:
                            json1[i]["content"] = new_json1
                        if len(new_json2) == 0:
                            json2[j] = None
                        else:
                            json2[j]["content"] = new_json2
                    elif item1["is_file"] != item2["is_file"]:##### Caso hipotetico imposible #####
                        json1[i]["tag"] == "delete"
    json1 = list(filter(None, json1))
    json2 = list(filter(None, json2))
    return json1, json2
if __name__ == "__main__":
    try:
        json1 = get_json("/home/kirbylife/Proyectos/munyal_test/original")
        json2 = get_json("/home/kirbylife/Proyectos/munyal_test/copy")
    except:
        print("error outside")
    json1, json2 = compare_json(json1, json2)
    #print(len(json1), len(json2))
    print(json.dumps(json1, indent=4))
    print("\n============\n")
    print(json.dumps(json2, indent=4))
