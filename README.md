# deduplication
# deduplication system using OpenCV and MD5 hashing algorithm

"""
deduplication helps to detect duplicate files before uploading them into the database, preventing the upload of duplicate file.
"""

"""
Requirements:
Python
OpenCV
MD5
Firebase
"""

from deduplication import DuplicateImage

if __name__ == '__main__':
    # Initialize the Duplicate module
    module = DuplicateImage()

    # Use the 'dup' function to detect duplicate images
    module.dup(image="image.jpg")

    # Use the 'detect' function to check for duplicates in a specific album
    status = module.detect(album="album_id", image="sample.jpg")

    print(status)

```
