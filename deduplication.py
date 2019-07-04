
from pymongo import MongoClient
import cv2 as cv
import hashlib

class DuplicateImage:

    def __init__(self):
        self.image = "IMG_0842.JPG"
        self.client = MongoClient("datbased_address")
        self.database = self.client["datbase_name"]
        self.collection = self.database["collection_name"]

    def dup(self, image):

        """
        :param image: input image to convert into  grayscale image..
        :return: will create image with sample.jpg name..
        """

        img = cv.imread(image, 0)
        (thresh, img_bin) = cv.threshold(img, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
        img_bin = 255 - img_bin
        cv.imwrite("sample.jpg", img_bin)

    # create hash from given new image and compare with already existing images to detect duplicates..
    def detect(self, image, album):
        """
        :param image: input new image to check duplication in the database..
        :param album: album which needs to scan the database to get the hash keys of the stored images..
        :return: returns two type of status{image exists in database or not} {de-duplication can be done or not}..
        """
        try:
            image_file = open(image, 'rb').read()
            key = hashlib.md5(image_file).hexdigest()

            # getting image hash keys from the database for relative images
            img = self.collection.find_one(album)

            hash_key = img["hash"]

            # this logic to be updated later while testing phase
            # matching the key with in the database or relative album
            if key == hash_key:
                isSuccess = False
                print("image already exists in the database!!!")
                return isSuccess
            else:
                isSuccess = True
                return isSuccess
        except Exception as ex:
            print("duplication can't be determined/ {}".format(ex))

            return 500
