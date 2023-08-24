from flask import Flask, render_template, send_file, request
import random
from flask_cors import CORS
import shutil

import os


DATA_DIR = "data/"
UNGROUPED_CLASS = "Ungrouped"


app = Flask(__name__)
CORS(app)

@app.route('/classes', methods = ["GET"])
def get_classes():
    res = os.listdir(DATA_DIR)
    res = [{"class" : i, "preview" : os.listdir(DATA_DIR + i)[0] if len(os.listdir(DATA_DIR + i))> 0 else None} for i in res if i != UNGROUPED_CLASS]

    return {"classes" : res}

@app.route('/class/<class_id>', methods = ["POST"])
def create_class(class_id):
    os.mkdir(DATA_DIR + class_id)
    return {"status" : "ok"}


@app.route('/classes/<class_id>', methods = ["GET"])
def get_class_files(class_id):
    res = os.listdir(DATA_DIR + class_id)

    return {"filenames" : res} 

@app.route('/file/<class_id>/<file_id>', methods = ["GET"])
def get_file(class_id, file_id):
    return send_file(DATA_DIR + class_id + "/" + file_id)


@app.route('/sort', methods= ["POST"])
def sort_files():
    print(request)
    data = request.get_json()
   
    print(data["files"])
    res = os.listdir(DATA_DIR + UNGROUPED_CLASS)
    res = [{"file" : i, "score" : random.random()} for i in res]
    res = list(reversed(sorted(res, key = lambda x : x["score"])))
    return {"files" : res}

@app.route('/move', methods= ["POST"])
def move_files():
    print(request)
    data = request.get_json()
    for file in data["files"]:
        shutil.move(DATA_DIR + UNGROUPED_CLASS + "/" + file["file"], DATA_DIR + data["class"] + "/" + file["file"])
    return {"status" : "ok"}




if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 3000)