from flask import Blueprint, send_from_directory, request
from flask_cors import CORS

from application import Application, UNSORTED_CLASS


def make_api(app: Application) -> Blueprint:
    api = Blueprint('Api', __name__, url_prefix='/api')
    CORS(api)

    @api.route('/classes', methods = ["GET"])
    def get_classes():
        classes = [
            {"name": cluster.name, "preview": cluster.preview}
            for cluster in app.clusters.values()
            if cluster.name != UNSORTED_CLASS
        ]
        return {"classes" : classes}


    @api.route('/class/<class_id>', methods = ["POST"])
    def create_class(class_id: str):
        app.create_cluster(class_id)
        return {"status" : "ok"}


    @api.route('/classes/<class_id>', methods = ["GET"])
    def get_class_files(class_id: str):
        return {"files" : app.get_cluster_items(class_id)} 


    @api.route('/file/<class_id>/<item_id>', methods = ["GET"])
    def serve_file(class_id: str, item_id: str):
        assert class_id in app.clusters
        assert item_id in app.clusters[class_id].items
        return send_from_directory(app.data_root, f'{class_id}/{item_id}', max_age=60*60*24)


    @api.route('/sort', methods=["POST"])
    def sort_files():
        data = request.get_json()
        result = app.sort(set(data["files"]))
        return {"files" : result}
    
    @api.route('/sort_by_class', methods=["POST"])
    def sort_files_by_class():
        data = request.get_json()
        result = app.sort_by_class(data["class"])
        return {"files" : result}

    @api.route('/move', methods= ["POST"])
    def move_files():
        data = request.get_json()
        dest_class = data["class"]
        if dest_class not in app.clusters:
            app.create_cluster(dest_class)
        app.unsorted2cluster(data["files"], dest_class)
        return {"status" : "ok"}
    
    return api
