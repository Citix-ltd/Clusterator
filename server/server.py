from flask import Flask, render_template, send_from_directory, request
import random
from flask_cors import CORS
import shutil
import os

from sorter import generate_embeddings, find_close_to_many, save_embeddings, read_embeddings


DATA_DIR = "data/"
UNGROUPED_CLASS = "Ungrouped"
FILES_LIMIT = 256


embeddings_cache = "embeddings.h5"
if os.path.exists(embeddings_cache):
    embeddings = read_embeddings(embeddings_cache)
else:
    embeddings = generate_embeddings(DATA_DIR + UNGROUPED_CLASS)
    save_embeddings(embeddings_cache, embeddings)


app = Flask(__name__)
CORS(app)


@app.route('/classes', methods = ["GET"])
def get_classes():
    res = os.listdir(DATA_DIR)
    res = [{"name" : i, "preview" : os.listdir(DATA_DIR + i)[0] if len(os.listdir(DATA_DIR + i))> 0 else None} for i in res if i != UNGROUPED_CLASS]
    return {"classes" : res}


@app.route('/class/<class_id>', methods = ["POST"])
def create_class(class_id: str):
    os.mkdir(DATA_DIR + class_id)
    return {"status" : "ok"}


@app.route('/classes/<class_id>', methods = ["GET"])
def get_class_files(class_id: str):
    res = os.listdir(DATA_DIR + class_id)[:FILES_LIMIT]
    return {"files" : res} 


@app.route('/file/<path:path>', methods = ["GET"])
def serve_file(path):
    return send_from_directory(DATA_DIR, path, max_age=60*60*24)


@app.route('/sort', methods=["POST"])
def sort_files():
    data = request.get_json()

    res = find_close_to_many(set(data["files"]), embeddings)
    res = list([r[0] for r in res])[:FILES_LIMIT]
    res = {"files" : res}
    return res


@app.route('/move', methods= ["POST"])
def move_files():
    data = request.get_json()
    print(data)
    dest_class = data["class"]
    if not os.path.exists(DATA_DIR + dest_class):
        os.mkdir(DATA_DIR + dest_class)
    for filename in data["files"]:
        from_path = os.path.join(DATA_DIR, UNGROUPED_CLASS, filename)
        to_path = os.path.join(DATA_DIR, dest_class, filename)
        shutil.move(from_path, to_path)
    return {"status" : "ok"}


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 3001)
