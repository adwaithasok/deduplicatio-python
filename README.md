# Image-deduplica
Image deduplication system using Opencv and MD5 hashing algorithm

```
Image-deduplica helps to detect the duplicate images before uploading into the database which helps to prevent uploaded duplicate images into database.
```
```
Requirements:
MongoDB
python
Opencv
MD5
```
```
Usage:
from deduplication import DuplicateImage
module = DuplicateImage()

module.dup(image= "image.jpg")

status = module.detect(album ="album_id", image= "sample.jpg")

print(status)
```
