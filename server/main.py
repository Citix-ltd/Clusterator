import os
import fire
from flask import Flask

from application import Application
from api_blueprint import make_api


class CliEntryPoint:
    def serve(self, data_root: str) -> None:
        if not os.path.isdir(data_root):
            raise ValueError(f"Data root {data_root} is not a directory")
        application = Application(data_root)
        api = make_api(application)

        flask_app = Flask(__name__)
        flask_app.register_blueprint(api)
        flask_app.run(host = "0.0.0.0", port = 3001)


if __name__ == "__main__":
    fire.Fire(CliEntryPoint)
