class DuplicateFile:
    def __init__(self, firebase_credentials_path):
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
            query = collection_ref.where('hash', '==', data_hash)
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

    def upload_data_to_user(self, register_number, data):
        try:
            # Check if the user with the given register number exists in Firestore
            users_ref = self.db.collection('users')
            query = users_ref.where('register_number', '==', register_number)
            docs = query.stream()

            user_doc = next(docs, None)
            if user_doc:
                # User found, update or create a new collection for the user
                user_data = user_doc.to_dict()
                user_album = f"{register_number}"
                status, _ = self.check_duplicate(data, user_album)
                if status:
                    return True, user_album
                else:
                    return False, None
            else:
                return False, None

        except Exception as ex:
            print(f"Upload data to user failed: {ex}")
            return False, None

    def download_data(self, data_hash, album):
        try:
            # Check if the collection exists
            collection_ref = self.db.collection(album)

            # Query for the document with the specified hash
            query = collection_ref.where('hash', '==', data_hash)
            docs = query.stream()

            for doc in docs:
                doc_data = doc.to_dict()
                return True, doc_data.get("data")

            # If the document with the specified hash is not found
            print("Data not found in the database.")
            return False, None

        except Exception as ex:
            print(f"Download failed: {ex}")
            return False, None


@app.route('/check_duplicate', methods=['POST'])
def check_duplicate_api():
    if 'data' not in request.files or 'register_number' not in request.form:
        return jsonify({'error': 'Invalid request. Make sure to include "data" and "register_number".'}), 400

    try:
        data_file = request.files['data']
        register_number = request.form['register_number']

        # Process the file data
        data = data_file.read()
        encoded_data = base64.b64encode(data).decode('utf-8')

        # Check for duplicate and upload to user's collection
        status, existing_data = duplicate_checker.upload_data_to_user(
            register_number, encoded_data)
        if status:
            if existing_data is None:
                return jsonify({'message': 'Data doesn\'t exist in the user\'s collection. Added successfully.'}), 200
            else:
                return jsonify({'message': 'Data already exists in the user\'s collection.', 'existing_data': existing_data}), 200
        else:
            return jsonify({'error': 'Error occurred while checking for duplicates or uploading to user\'s collection.'}), 500

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500


@app.route('/download_data', methods=['GET'])
def download_data_api():
    data_hash = request.args.get('data_hash')
    register_number = request.args.get('register_number')

    if not data_hash or not register_number:
        return jsonify({'error': 'Invalid request. Make sure to include "data_hash" and "register_number".'}), 400

    try:
        # Download data from user's collection
        user_album = f"user_{register_number}"
        success, downloaded_data = duplicate_checker.download_data(
            data_hash, user_album)

        if success:
            return send_file(downloaded_data, as_attachment=True), 200
        else:
            return jsonify({'error': 'Download failed.'}), 404

    except Exception as ex:
        return jsonify({'error': f'Error: {ex}'}), 500
