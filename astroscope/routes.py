from flask import Blueprint, jsonify, send_from_directory, redirect, request



sites = Blueprint('main', __name__)
# note the lack of a url_prefix parameter

@sites.route("/api/hello")
def hello_world():
    return jsonify({'message': "Hello World"})

@sites.route("/home")
def home():
    return "AstroScope"

@sites.route('/main')
def main_page():
    path = 'index.html'
    print(path)
    return send_from_directory('static', path=path)

@sites.route('/map')
def impact_map():
    path = 'impact_map.html'
    print(path)
    return send_from_directory('static', path=path)

@sites.route('/')
def base():
    return redirect('/main')
