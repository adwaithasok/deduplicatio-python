# deduplication system using OpenCV and MD5 hashing algorithm

# Duplicate File Detection System

This system allows users to check for and prevent the upload of duplicate files to a database. It leverages the MD5 hashing algorithm and the `magic` library for MIME type detection. The system is designed to work with Firebase as the database service.


### Setup

Ensure you have the following installed:

- Python
- Firebase Admin SDK
- `magic` library

### Configuration

1. Provide the path to your Firebase service account credentials JSON file. Replace the path in the `firebase_credentials_path` variable in the script.

2. Specify the name of the album in the `check_duplicate` function call in the example usage section. Replace the `"Abhinav"` placeholder with your desired album name.

### Example Usage

```python
if __name__ == '__main__':
    # Provide the path to your Firebase service account credentials JSON file
    firebase_credentials_path = "credentials.json"  # Replace with your Firebase credentials path

    d = DuplicateFile(firebase_credentials_path)
    with open("sample.jpg", "rb") as file:
        file_data = file.read()
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        status, _ = d.check_duplicate(encoded_data, "Abhinav")  # Replace with your album name
        if status:
            print("Data doesn't exist in the database. Added successfully.")
        else:
            print("Data already exists in the database.")

