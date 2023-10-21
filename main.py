from flask import Flask, request, jsonify
import base64
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
import magic

app = Flask(__name__)


class DuplicateFile:
    def __init__(self, firebase_credentials_path):
        # Initialize Firebase
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def generate_hash(self, data):
        return hashlib.md5(data).hexdigest()

    def check_duplicate(self, data, album):
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
                    return False, doc_data.get("data")

            # If the data does not exist, create a new document in the collection
            if len(data_bytes) > 1048487:
                print(
                    "Data size exceeds limit. Consider storing in chunks or in storage services.")
                return False, None

            mime_type = magic.from_buffer(data_bytes, mime=True)
            document_data = {'hash': data_hash,
                             'data': data, 'mime_type': mime_type}
            collection_ref.add(document_data)
            return True, None

        except Exception as ex:
            print(f"Duplicate check failed: {ex}")
            return False, None


# Initialize the DuplicateFile class
# Replace with your Firebase credentials path
# Replace with your Firebase credentials path
firebase_credentials_path = "credentials.json"
d = DuplicateFile(firebase_credentials_path)


@app.route('/check_duplicate', methods=['POST'])
def check_duplicate_api():
    if 'data' not in request.files or 'album' not in request.form:
        return jsonify({'error': 'Invalid request. Make sure to include "data" and "album".'}), 400

    try:
        data_file = request.files['data']
        album = request.form['album']

        # Process the file data
        data = data_file.read()
        encoded_data = base64.b64encode(data).decode('utf-8')

        # Check for duplicate
        status, existing_data = d.check_duplicate(encoded_data, album)

        if status:
            if existing_data is None:
                return jsonify({'message': 'Data doesn\'t exist in the database. Added successfully.'}), 200
        else:
            return jsonify({'message': 'Data already exists in the database.', 'existing_data': existing_data}), 200

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
