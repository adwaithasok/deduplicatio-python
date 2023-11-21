from flask import Flask, request, jsonify
from flask import Flask, request, jsonify, abort
import base64
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
import magic
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


class DuplicateFile:
    def __init__(self, firebase_credentials_path):
        # Initialize Firebase
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def generate_hash(self, data):
        return hashlib.md5(data).hexdigest()

    def check_duplicate(self, data, register_number):
        try:
            data_bytes = base64.b64decode(data.encode('utf-8'))
            data_hash = self.generate_hash(data_bytes)

            # Check if the collection exists
            collection_ref = self.db.collection(register_number)
            users_ref = duplicate_checker.db.collection('users')
            query = users_ref.where('register_number', '==', register_number)

            # If the collection exists, check if the data exists in any document within the collection
            # query = collection_ref.where('hash', '==', data_hash)
            query = users_ref.where(
                'register_number', '==', register_number)

            docs = query.stream()

            for doc in docs:
                doc_data = doc.to_dict()
                print("Data already exists in the database!!!")
                return True, doc_data.get("data")

            # If the data does not exist, create a new document in the collection
            if len(data_bytes) > 1048487:
                print(
                    "Data size exceeds limit. Consider storing in chunks or in storage services.")
                return False, None

            mime_type = magic.Magic()
            mime_type_value = mime_type.from_buffer(data_bytes)
            document_data = {'hash': data_hash,
                             'data': data, 'mime_type': mime_type_value}
            collection_ref.add(document_data)
            return True, None

        except Exception as ex:
            print(f"Duplicate check failed: {ex}")
            return False, None

# class DuplicateFile:
#     def __init__(self, firebase_credentials_path):
#         cred = credentials.Certificate(firebase_credentials_path)
#         firebase_admin.initialize_app(cred)
#         self.db = firestore.client()

#     def generate_hash(self, data):
#         return hashlib.md5(data).hexdigest()

#     def check_duplicate(self, data, album):
#         try:
#             data_bytes = base64.b64decode(data.encode('utf-8'))
#             data_hash = self.generate_hash(data_bytes)

#             # Check if the collection exists
#             collection_ref = self.db.collection(album)

#             # If the collection exists, check if the data exists in any document within the collection
#             query = collection_ref.where('hash', '==', data_hash)
#             docs = query.stream()

#             for doc in docs:
#                 doc_data = doc.to_dict()
#                 print("Data already exists in the database!!!")
#                 return True, doc_data.get("data")

#             # If the data does not exist, create a new document in the collection
#             if len(data_bytes) > 1048487:
#                 print(
#                     "Data size exceeds limit. Consider storing in chunks or in storage services.")
#                 return False, None

#             mime_type = magic.Magic()
#             mime_type_value = mime_type.from_buffer(data_bytes)
#             document_data = {'hash': data_hash,
#                              'data': data, 'mime_type': mime_type_value}
#             collection_ref.add(document_data)
#             return True, None

#         except Exception as ex:
#             print(f"Duplicate check failed: {ex}")
#             return False, None

#     def upload_data_to_user(self, register_number, data):
#         try:
#             # Check if the user with the given register number exists in Firestore
#             users_ref = self.db.collection('users')
#             query = users_ref.where('register_number', '==', register_number)
#             docs = query.stream()

#             user_doc = next(docs, None)
#             if user_doc:
#                 # User found, update or create a new collection for the user
#                 user_data = user_doc.to_dict()
#                 user_album = f"{register_number}"
#                 status, _ = self.check_duplicate(data, user_album)
#                 if status:
#                     return True, user_album
#                 else:
#                     return False, None
#             else:
#                 return False, None

#         except Exception as ex:
#             print(f"Upload data to user failed: {ex}")
#             return False, None

#     def download_data(self, data_hash, album):
#         try:
#             # Check if the collection exists
#             collection_ref = self.db.collection(album)

#             # Query for the document with the specified hash
#             query = collection_ref.where('hash', '==', data_hash)
#             docs = query.stream()

#             for doc in docs:
#                 doc_data = doc.to_dict()
#                 return True, doc_data.get("data")

#             # If the document with the specified hash is not found
#             print("Data not found in the database.")
#             return False, None

#         except Exception as ex:
#             print(f"Download failed: {ex}")
#             return False, None


# Initialize the DuplicateFile class
# Replace with your Firebase credentials path
firebase_credentials_path = "credentials.json"
duplicate_checker = DuplicateFile(firebase_credentials_path)


@app.route('/register', methods=['POST'])
def register_user():
    if 'register_number' not in request.json or 'name' not in request.json or 'dob' not in request.json or 'department' not in request.json:
        return jsonify({'error': 'Invalid request. Make sure to include "register_number", "name", "dob", and "department".'}), 400

    try:
        register_number = request.json['register_number']
        name = request.json['name']
        dob = request.json['dob']
        department = request.json['department']

        # Check if the user with the given register_number already exists in Firestore
        users_ref = duplicate_checker.db.collection('users')
        query = users_ref.where('register_number', '==', register_number)
        docs = query.stream()

        if len(list(docs)) > 0:
            return jsonify({'error': 'User with this register number already exists.'}), 400

        # Create a new user document in Firestore
        user_data = {
            'register_number': register_number,
            'name': name,
            'dob': dob,
            'department': department
        }
        users_ref.add(user_data)

        return jsonify({'message': 'User registered successfully.'}), 200

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


@app.route('/login', methods=['POST'])
def login_user():
    if 'register_number' not in request.json or 'dob' not in request.json:
        return jsonify({'error': 'Invalid request. Make sure to include "register_number" and "dob".'}), 400

    try:
        register_number = request.json['register_number']
        dob = request.json['dob']

        # Check if the user with the given register_number and dob exists in Firestore
        users_ref = duplicate_checker.db.collection('users')
        query = users_ref.where('register_number', '==',
                                register_number).where('dob', '==', dob)
        docs = query.stream()

        if len(list(docs)) > 0:
            return jsonify({'message': 'Login successful.'}), 200
        else:
            return jsonify({'error': 'Invalid register number or date of birth.'}), 401

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 401


@app.route('/get_all_users', methods=['GET'])
def get_all_users():
    try:
        # Retrieve all documents from the "users" collection
        users_ref = duplicate_checker.db.collection('users')
        docs = users_ref.stream()

        # Extract data from each document
        all_users_data = [doc.to_dict() for doc in docs]

        return jsonify({'users_data': all_users_data}), 200

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


@app.route('/get_registration_data', methods=['GET'])
def get_registration_data():
    register_number = request.args.get('register_number')
    dob = request.args.get('dob')

    if not register_number or not dob:
        return jsonify({'error': 'Invalid request. Make sure to include "register_number" and "dob".'}), 400

    try:
        # Check if the user with the given register_number and dob exists in Firestore
        users_ref = duplicate_checker.db.collection('users')
        query = users_ref.where('register_number', '==',
                                register_number).where('dob', '==', dob)
        docs = query.stream()

        first_doc = next(docs, None)
        if first_doc:
            # Retrieve the user's registration data
            user_data = first_doc.to_dict()
            return jsonify({'message': 'Login successful.', 'registration_data': user_data}), 200
        else:
            return jsonify({'error': 'Invalid register number or date of birth.'}), 401

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 401


# Assuming you have the DuplicateFile class and its instantiation here


@app.route('/assign_work', methods=['POST'])
def assign_work():
    if 'register_numbers' not in request.json or 'work_details' not in request.json:
        return jsonify({'error': 'Invalid request. Make sure to include "register_numbers" and "work_details".'}), 400

    try:
        register_numbers = request.json['register_numbers']
        work_details = request.json['work_details']

        # Check if each user with the given register numbers exists in Firestore
        users_ref = duplicate_checker.db.collection('users')

        success_messages = []
        error_messages = []

        for register_number in register_numbers:
            query = users_ref.where('register_number', '==', register_number)
            docs = query.stream()

            user_doc = next(docs, None)
            if user_doc:
                # User found, update or create a new "work" field in the user's document
                user_data = user_doc.to_dict()
                user_data['work'] = work_details
                user_doc.reference.set(user_data)
                success_messages.append(
                    f'Work assigned successfully for user with register number {register_number}.')
            else:
                error_messages.append(
                    f'User not found with register number {register_number}.')

        if error_messages:
            return jsonify({'errors': error_messages}), 404
        else:
            return jsonify({'success': success_messages}), 200

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


# @app.route('/check_duplicate', methods=['POST'])
# def check_duplicate_api():
#     if 'data' not in request.files or 'register_number' not in request.form:
#         return jsonify({'error': 'Invalid request. Make sure to include "data" and "register_number".'}), 400

#     try:
#         data_file = request.files['data']
#         register_number = request.form['register_number']

#         # Process the file data
#         data = data_file.read()
#         encoded_data = base64.b64encode(data).decode('utf-8')

#         # Check for duplicate and upload to user's collection
#         status, existing_data = duplicate_checker.upload_data_to_user(
#             register_number, encoded_data)
#         if status:
#             if existing_data is None:
#                 return jsonify({'message': 'Data doesn\'t exist in the user\'s collection. Added successfully.'}), 200
#             else:
#                 return jsonify({'message': 'Data already exists in the user\'s collection.', 'existing_data': existing_data}), 200
#         else:
#             return jsonify({'error': 'Error occurred while checking for duplicates or uploading to user\'s collection.'}), 500

#     except Exception as ex:
#         return jsonify({'error': f'Error: {ex}'}), 500


# @app.route('/download_data', methods=['GET'])
# def download_data_api():
#     data_hash = request.args.get('data_hash')
#     register_number = request.args.get('register_number')

#     if not data_hash or not register_number:
#         return jsonify({'error': 'Invalid request. Make sure to include "data_hash" and "register_number".'}), 400

#     try:
#         # Download data from user's collection
#         user_album = f"user_{register_number}"
#         success, downloaded_data = duplicate_checker.download_data(
#             data_hash, user_album)

#         if success:
#             return send_file(downloaded_data, as_attachment=True), 200
#         else:
#             return jsonify({'error': 'Download failed.'}), 404

#     except Exception as ex:
#         return jsonify({'error': f'Error: {ex}'}), 500

@app.route('/check_duplicate', methods=['POST'])
def check_duplicate_api():
    if 'data' not in request.files or 'album' not in request.form:
        return jsonify({'error': 'Invalid request. Make sure to include "data" and "album".'}), 400

    try:
        data_file = request.files['data']
        register_number = request.json['register_number']

        # Process the file data
        data = data_file.read()
        encoded_data = base64.b64encode(data).decode('utf-8')

        # Check for duplicate
        status, existing_data = duplicate_checker.check_duplicate(
            encoded_data, register_number)
        print(status)
        print(existing_data)

        if status:
            if existing_data is None:
                return jsonify({'message': 'Data doesn\'t exist in the database. Added successfully.'}), 200
            else:
                return jsonify({'message': 'Data already exists in the database.', 'existing_data': existing_data}), 200
        else:
            return jsonify({'error': 'Error occurred while checking for duplicates.'}), 500

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
