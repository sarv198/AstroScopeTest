import requests
from flask_caching import Cache
from flask import Flask
from flask_cors import CORS


'''
Purpose:
Entry point and set up for Flask app
'''
cache = Cache()

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.update({
        "CACHE_TYPE": "FileSystemCache",  # or "DiskCacheCache" if you installed flask-caching[diskcache]
        "CACHE_DIR": "./neo_cache",
        "CACHE_DEFAULT_TIMEOUT": 3600
    })

    cache.init_app(app)
    
    # register Blueprint containing routes
    from routes import sites
    app.register_blueprint(sites)

    from api import api
    app.register_blueprint(api)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)



