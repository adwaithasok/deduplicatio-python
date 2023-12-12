import dbm
from flask import send_file, make_response
from flask import send_file
from flask import Flask, request, jsonify, send_file
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

    def delete_user(self, register_number):
        try:
            users_ref = self.db.collection('users')

            # Check if the user with the given register_number exists
            query = users_ref.where('register_number', '==', register_number)
            docs = query.stream()

            user_doc = next(docs, None)

            if not user_doc:
                return False, {'error': 'User not found with the specified register number.'}

            # Delete the user document
            user_doc.reference.delete()
            return True, {'message': 'User deleted successfully.'}

        except Exception as ex:
            return False, {'error': f'Error: {ex}'}

    def generate_hash(self, data):
        return hashlib.md5(data).hexdigest()

    def check_duplicate(self, data, album, register_number, work_number):
        try:
            data_bytes = base64.b64decode(data.encode('utf-8'))
            data_hash = self.generate_hash(data_bytes)

            # Check if the collection exists
            collection_ref = self.db.collection(album)

            # If the collection exists, check if the data exists in any document within the collection
            all_docs = collection_ref.stream()

            for doc in all_docs:
                doc_data = doc.to_dict()
                if 'hash' in doc_data and doc_data['hash'] == data_hash:
                    print("Data already exists in the database!!!")
                    if register_number != doc_data['register_number']:
                        document_data = {'isDuplicateHappend': True,
                                         'register_number': register_number}
                        collection_ref.add(document_data)
                    return True, ""

            # If the data does not exist, create a new document in the collection
            if len(data_bytes) > 1048487:
                print(
                    "Data size exceeds limit. Consider storing in chunks or in storage services.")
                return False, None

            mime_type = magic.Magic()
            mime_type_value = mime_type.from_buffer(data_bytes)
            document_data = {'hash': data_hash,
                             'data': data, 'mime_type': mime_type_value, 'register_number': register_number, 'work_number': work_number}
            collection_ref.add(document_data)
            return True, None

        except Exception as ex:
            print(f"Duplicate check failed: {ex}")
            return False, None


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


@app.route('/edit_user', methods=['PUT'])
def edit_user():
    try:
        db = firestore.client()  # Add this line to declare db as a global variable
        if 'register_number' not in request.json:
            return jsonify({'error': 'Invalid request. Make sure to include "register_number".'}), 400

        register_number = request.json['register_number']
        users_ref = db.collection('users')

        # Check if the user with the given register_number exists
        query = users_ref.where('register_number', '==', register_number)
        docs = query.stream()

        user_doc = next(docs, None)

        if not user_doc:
            return jsonify({'error': 'User not found with the specified register number.'}), 404

        # Update user data
        updated_data = request.json.get('updated_data', {})
        user_doc.reference.update(updated_data)

        return jsonify({'message': 'User data updated successfully.'}), 200

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


@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    if 'register_number' not in request.json:
        return jsonify({'error': 'Invalid request. Make sure to include "register_number".'}), 400

    try:
        register_number = request.json['register_number']
        status, response = duplicate_checker.delete_user(register_number)

        if status:
            return jsonify(response), 200
        else:
            return jsonify(response), 404

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


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
        work_number = request.json['work_number']

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
                user_data['workNumber'] = work_number

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


@app.route('/check_duplicate', methods=['POST'])
def check_duplicate_api():
    if 'data' not in request.files or 'album' not in request.form:
        return jsonify({'error': 'Invalid request. Make sure to include "data" and "album".'}), 400

    try:
        data_file = request.files['data']
        album = request.form['album']
        register_nnumber = request.form['register_number']
        work_number = request.form['work_number']

        # Process the file data
        data = data_file.read()
        encoded_data = base64.b64encode(data).decode('utf-8')

        # Check for duplicate
        # status, existing_data = d.check_duplicate(encoded_data, album)
        # Check for duplicate
        status, existing_data = duplicate_checker.check_duplicate(
            encoded_data, album, register_nnumber, work_number)

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

# Assume your /download_data endpoint fetches data from the "hello" collection for a given register_number


@app.route('/download_data', methods=['GET'])
def download_data():
    register_number = request.args.get('register_number')

    if not register_number:
        return jsonify({'error': 'Invalid request. Make sure to include "register_number".'}), 400

    try:
        users_ref = duplicate_checker.db.collection('AssignmentCS')

        query = users_ref.where('register_number', '==', register_number)
        docs = query.stream()

        # Check if any documents exist
        if not docs:
            return jsonify({'error': 'User not found with the specified register number.'}), 404

        # Assuming there could be multiple documents, iterating over them
        for doc in docs:
            # Extract data from the document
            user_data_dict = doc.to_dict()

            # Assume your data is stored in a 'data' field in the document
            data_to_download = user_data_dict.get('data', '')

            # Decode Base64
            decoded_data = base64.b64decode(data_to_download)

            # Get the MIME type dynamically, defaulting to 'application/octet-stream'
            mime_type = user_data_dict.get(
                'mime_type')

            # Save the data to a local file
            # Adjust the file extension based on MIME type
            local_filename = f'{register_number}.{mime_type.split("/")[1]}'
            with open(local_filename, 'wb') as file:
                file.write(decoded_data)

            # Return the file as a response with the appropriate headers
            response = make_response(send_file(local_filename))
            response.headers['Content-Type'] = mime_type
            response.headers['Content-Disposition'] = f'attachment; filename={local_filename}'
            return response, 200

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500

    return jsonify({'error': 'User not found with the specified register number.'}), 404


@app.route('/check_upload_status', methods=['GET'])
def check_upload_status():
    register_number = request.args.get('register_number')

    if not register_number:
        return jsonify({'error': 'Invalid request. Make sure to include "register_number".'}), 400

    try:
        users_ref = duplicate_checker.db.collection('AssignmentCS')

        query = users_ref.where('register_number', '==', register_number)
        docs = query.stream()

        # Check if any documents exist for the specified register number
        dosc_resp = {}
        for doc in docs:
            user_data_dict = doc.to_dict()
            print("hello", user_data_dict)
            if doc.id is not None:
                dosc_resp['document_id'] = doc.id
            if user_data_dict.get('data', '') != "":
                dosc_resp['data'] = user_data_dict.get('data', '')
            if user_data_dict.get('mime_type', '') != "":
                dosc_resp['mime_type'] = user_data_dict.get('mime_type', '')
            if user_data_dict.get('workNumber', '') != "":
                dosc_resp['work_number'] = user_data_dict.get('workNumber', '')
            if user_data_dict.get('isDuplicateHappend', '') != "":
                dosc_resp['isDuplicateHappend'] = user_data_dict.get(
                    'isDuplicateHappend', '')
            if user_data_dict.get('register_number', '') != "":
                dosc_resp['register_number'] = user_data_dict.get(
                    'register_number', '')

        if dosc_resp.get("data", "") == "":
            return jsonify({'status': False, 'message': 'No data uploaded for the specified register number.', 'uploaded_data': dosc_resp}), 200
        else:
            return jsonify({'status': True, 'message': 'Data uploaded for the specified register number.', 'uploaded_data': dosc_resp}), 200

    except Exception as ex:
        return jsonify({'status': False, 'error': f'Error: {ex}'}), 500


# @app.route('/download_data', methods=['GET'])
if __name__ == '__main__':
    app.run(debug=True)
