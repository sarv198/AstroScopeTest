from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route("/api/hello")
def hello_world():
    return jsonify({'message': "Hello World"})

@app.route('/api/neo')
def neo_data():
    content = request.json
    # parse the content for key info: filters, api to request
    # ...
    
    # use the nasa_api.py
    data = 0 

    return jsonify({'data': data})



if __name__ == "__main__":
    app.run(debug=True)


