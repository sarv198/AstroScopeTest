import requests
from flask_caching import Cache
from flask import Flask
from flask_cors import CORS
from extensions import cache

'''
Purpose:
Entry point and set up for Flask app
'''


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.update({
        "CACHE_TYPE": "FileSystemCache",
        "CACHE_DIR": "./neo_cache",
        "CACHE_DEFAULT_TIMEOUT": 3600
    })

    cache.init_app(app)
    
    # register Blueprint containing routes
    from sites import sites
    from api import api
    from sim import sim

    app.register_blueprint(sites)
    app.register_blueprint(api)
    app.register_blueprint(sim)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
