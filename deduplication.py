import base64
import hashlib
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


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
            data_bytes = data.encode('utf-8')
            data_hash = self.generate_hash(data_bytes)

            # Check if the data exists in Firestore
            doc_ref = self.db.collection(album).document('file_data')
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                hash_key = data.get("hash")

                if data_hash == hash_key:
                    print("Data already exists in the database!!!")
                    return False, data.get("data")
                else:
                    doc_ref.set({'hash': data_hash, 'data': data})
                    return True, None
            else:
                doc_ref.set({'hash': data_hash, 'data': data})
                return True, None

        except Exception as ex:
            print(f"Duplicate check failed: {ex}")
            return False, None

    def retrieve_data_from_hash(self, data_hash, album, download_path):
        try:
            doc_ref = self.db.collection(album).document('file_data')
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                hash_key = data.get("hash")

                if data_hash == hash_key:
                    # Retrieve the original data from the hash
                    retrieved_data = data.get("data")
                    with open(download_path, "wb") as file:
                        file.write(base64.b64decode(retrieved_data))
                    return download_path
                else:
                    print("Data with the specified hash not found!")
                    return None
            else:
                print("No data found in the specified album!")
                return None

        except Exception as ex:
            print(f"Data retrieval failed: {ex}")
            return None


# Example usage:
if __name__ == '__main__':
    # Provide the path to your Firebase service account credentials JSON file
    firebase_credentials_path = "credentials.json"  # Replace with your Firebase credentials path

    d = DuplicateFile(firebase_credentials_path)
    with open("sample.jpg", "rb") as file:
        image_data = base64.b64encode(file.read()).decode('utf-8')
        status, file_data = d.check_duplicate(image_data, "Abhinav")  # Replace with your album name
        if status:
            retrieved_file_path = d.retrieve_data_from_hash(d.generate_hash(image_data.encode('utf-8')), "Abhinav", "retrieved_sample.jpg")  # Replace with your album name and desired download path
            if retrieved_file_path:
                print(f"Data retrieved successfully. File downloaded to: {retrieved_file_path}")
            else:
                print("Failed to retrieve the data.")
        else:
            print("Data already exists in the database.")
