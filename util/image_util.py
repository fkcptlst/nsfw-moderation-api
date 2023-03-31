from typing import List, Tuple
from os import listdir
from os.path import isfile, join, isdir, abspath

from nsfw_detector.predict import IMAGE_DIM
from tensorflow import keras
import numpy as np


def load_images(image_paths: List[str], image_size: Tuple[int, int] = (IMAGE_DIM, IMAGE_DIM), verbose: bool = True):
    '''
    Function for loading images into numpy arrays for passing to model.predict
    inputs:
        image_paths: list of image paths to load
        image_size: size into which images should be resized
        verbose: show all the image path and sizes loaded

    outputs:
        loaded_images: loaded images on which keras model can run predictions
        loaded_image_indexes: paths of images which the function is able to process
    '''
    loaded_images = []
    loaded_image_paths = []

    # if isdir(image_paths):
    #     parent = abspath(image_paths)
    #     image_paths = [join(parent, f) for f in listdir(image_paths) if isfile(join(parent, f))]
    # elif isfile(image_paths):
    #     image_paths = [image_paths]

    for img_path in image_paths:
        try:
            if verbose:
                print(img_path, "size:", image_size)
            image = keras.preprocessing.image.load_img(img_path, target_size=image_size)
            image = keras.preprocessing.image.img_to_array(image)
            image /= 255
            loaded_images.append(image)
            loaded_image_paths.append(img_path)
        except Exception as ex:
            print("Image Load Failure: ", img_path, ex)
            loaded_image_paths.append(None)

    return np.asarray(loaded_images), loaded_image_paths
