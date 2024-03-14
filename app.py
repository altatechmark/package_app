from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.json_util import dumps

app = Flask(__name__)
# Replace 'your_mongodb_uri' with your actual MongoDB URI
app.config["MONGO_URI"] = "mongodb+srv://shamoilkazmi:WrOupdeZVa2ElJVq@cluster0.j6b7l7r.mongodb.net/user"
mongo = PyMongo(app)


@app.route('/')
def hello():
    return 'Hello, World!'

# Endpoint to sign up a new user
@app.route('/signup', methods=['POST'])
def signup():
    users = mongo.db.users  # Accessing the users collection
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')  # Assuming you are passing email in JSON
    password = data.get('password')

    # Check if the username or email already exists in the database
    if users.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({'message': 'Username or email already exists'}), 400

    hashed_password = generate_password_hash(password)
    # Adding package_id as an empty field for future use
    users.insert_one({
        'username': username, 
        'email': email, 
        'password_hash': hashed_password,
        'package_id': None  # Or '' if you prefer an empty string
    })

    return jsonify({'message': 'User created successfully'}), 201


# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    data = request.get_json()
    user = users.find_one({"username": data.get('username')})

    if user and check_password_hash(user['password_hash'], data.get('password')):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# Endpoint to get all users
# Endpoint to get all users
@app.route('/users', methods=['GET'])
def get_users():
    users = mongo.db.users
    user_list = []
    for user in users.find():
        user_list.append({
            'id': str(user['_id']),
            'username': user['username'],
            'email': user.get('email', 'N/A'),  # Email will be shown, 'N/A' if not exist
            'package_id': user.get('package_id', 'Not assigned')  # Get package_id, default to 'Not assigned' if not exist
        })
    return jsonify({'users': user_list}), 200


# Route to get all packages
@app.route('/packages', methods=['GET'])
def get_packages():
    packages = mongo.db.packages
    package_list = []
    for package in packages.find():
        package_list.append({'package_id': package['package_id'], 'motion_status': package['motion_status'],
                             'box_lock_status': package['box_lock_status'], 'box_code': package['box_code']})
    return jsonify({'packages': package_list}), 200

# Route to add a new package
@app.route('/packages', methods=['POST'])
def add_package():
    packages = mongo.db.packages
    data = request.get_json()
    # It's important to validate data here for a real application
    package_id = data.get('package_id')
    motion_status = data.get('motion_status', False)  # Defaulting to False if not provided
    box_lock_status = data.get('box_lock_status', False)  # Defaulting to False if not provided
    box_code = data.get('box_code')

    if packages.find_one({"package_id": package_id}):
        return jsonify({'message': 'Package already exists'}), 400
    
    packages.insert_one({'package_id': package_id, 'motion_status': motion_status,
                         'box_lock_status': box_lock_status, 'box_code': box_code})
    return jsonify({'message': 'Package added successfully'}), 201

# Route to update a specific package detail by package_id
# For example, updating motion_status
@app.route('/packages/motion_status/<package_id>', methods=['PUT'])
def update_motion_status(package_id):
    packages = mongo.db.packages
    data = request.get_json()
    new_motion_status = data.get('motion_status')

    result = packages.update_one({'package_id': package_id}, {'$set': {'motion_status': new_motion_status}})
    if result.modified_count:
        return jsonify({'message': 'Motion status updated successfully'}), 200
    else:
        return jsonify({'message': 'No changes made or package not found'}), 400

# Route to update box_lock_status by package_id
@app.route('/packages/box_lock_status/<package_id>', methods=['PUT'])
def update_box_lock_status(package_id):
    packages = mongo.db.packages
    data = request.get_json()
    new_box_lock_status = data.get('box_lock_status')  # This should be a boolean value

    result = packages.update_one({'package_id': package_id}, {'$set': {'box_lock_status': new_box_lock_status}})
    if result.modified_count:
        return jsonify({'message': 'Box lock status updated successfully'}), 200
    else:
        return jsonify({'message': 'No changes made or package not found'}), 400

# Route to update box_code by package_id
@app.route('/packages/box_code/<package_id>', methods=['PUT'])
def update_box_code(package_id):
    packages = mongo.db.packages
    data = request.get_json()
    new_box_code = data.get('box_code')  # This should be a string or numerical code

    result = packages.update_one({'package_id': package_id}, {'$set': {'box_code': new_box_code}})
    if result.modified_count:
        return jsonify({'message': 'Box code updated successfully'}), 200
    else:
        return jsonify({'message': 'No changes made or package not found'}), 400

# Route to update user's package_id using user_id
@app.route('/users/<user_id>/package', methods=['PUT'])
def update_user_package_by_id(user_id):
    users = mongo.db.users
    data = request.get_json()
    new_package_id = data.get('package_id')

    # Convert user_id from string to ObjectId for MongoDB
    from bson import ObjectId
    if not ObjectId.is_valid(user_id):  # Validates whether the user_id is a valid ObjectId
        return jsonify({'message': 'Invalid user_id format'}), 400

    result = users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'package_id': new_package_id}}
    )

    if result.modified_count:
        return jsonify({'message': 'User package_id updated successfully'}), 200
    else:
        return jsonify({'message': 'User not found or package_id already set to this value'}), 404


    
# Route to get user's package_id by username
@app.route('/users/package/<username>', methods=['GET'])
def get_user_package_id(username):
    users = mongo.db.users
    user = users.find_one({"username": username})
    
    if user:
        # Check if 'package_id' exists for the user, if not, return a default message or value
        package_id = user.get('package_id', 'No package assigned')
        return jsonify({'username': username, 'package_id': package_id}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# Route to delete all users
@app.route('/users', methods=['DELETE'])
def delete_all_users():
    result = mongo.db.users.delete_many({})
    if result.deleted_count > 0:
        return jsonify({'message': f'{result.deleted_count} users deleted successfully'}), 200
    else:
        return jsonify({'message': 'No users found to delete'}), 404


if __name__ == '__main__':
    app.run(debug=True)
