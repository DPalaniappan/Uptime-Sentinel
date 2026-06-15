import validators
from flask import request, jsonify, Blueprint
from ..services import tracker_service

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def list_of_all_targets():
    targets = tracker_service.get_all_targets()
    return redirect()

@main.route('/target', methods=['POST'])
def add_target():
    data = request.get_json() 
    url = data.get('url')

    if not data or not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    result, status_code = tracker_service.add_new_target(url)
    return jsonify(result), status_code

@main.route('/track', methods=['POST'])
def track_targets():
    data = request.get_json()
    email = data.get('email')
    targets = data.get('targets', [])
    if not data or not email:
        return jsonify({'error': 'Email is required'}), 400
    
    if not validators.email(email):
        return jsonify({'error': 'Invalid email address'}), 400
    
    result, status_code = tracker_service.process_user_tracking(email, targets)
    return jsonify(result), status_code
    

@main.route('/ping/', methods=['GET'])
def get_targets():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), 400   
    
    result, status_code = tracker_service.get_ping_logs_for_target(url)
    return jsonify(result), status_code


@main.route('/user/targets', methods=['GET'])
def get_user_targets():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not validators.email(email):
        return jsonify({'error': 'Invalid email address'}), 400
    
    result, status_code = tracker_service.get_user_targets(email)
    return jsonify(result), status_code
    