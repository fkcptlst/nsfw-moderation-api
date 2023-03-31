# NSFW image moderation api

## What is this?

A simple self-hosted api for NSFW image detection. It uses Keras models
from [nsfw_model](https://github.com/GantMan/nsfw_model)
for inference.

You simply upload an image via `POST` request and get the probabilities of each class.

There are 5 classes available, see the example below.

## Features

- [x] single image and multiple images classification
- [x] cache images with sqlite3 for repeated requests
- [x] fastapi server with uvicorn

## How to use?

### single image classification

**upload**: `/classify`

```
POST /classify HTTP/1.1
Content-Type: multipart/form-data
```

**return**: json with the image name and the probabilities of each class

```json
{
  '1.png': {
    'drawings': 0.9876018166542053,
    'hentai': 0.012362617999315262,
    'neutral': 9.287304237659555e-06,
    'porn': 7.971775630721822e-07,
    'sexy': 2.5433639166294597e-05
  }
}
```

### multiple images classification

**upload**: `/classify-many`

```
POST /classify-many HTTP/1.1
Content-Type: multipart/form-data
```

**return**: list of dict with the image name and the probabilities of each class

```json
[
  {
    '1.png': {
      'drawings': 0.9876018166542053,
      'hentai': 0.012362617999315262,
      'neutral': 9.287304237659555e-06,
      'porn': 7.971775630721822e-07,
      'sexy': 2.5433639166294597e-05
    }
  },
  {
    '2.png': {
      'drawings': 0.9999114274978638,
      'hentai': 8.860819070832804e-05,
      'neutral': 3.5102059037228628e-09,
      'porn': 4.303543299499779e-09,
      'sexy': 6.545478603570132e-10
    }
  }
]
```

### Example with python requests

1. start the api server

```bash
python main.py
```

2. send a post request to the server with the image as a file(see python example below)

```python
import requests
import os

import requests

api_url_path = 'http://localhost:3000'  # change this to your api url

# images are stored locally in the 'images' folder
images_path = os.listdir('images')
images_path = [os.path.join('images', img_path) for img_path in images_path]


# single image classification
def api_single_image(img_path):
    files = {'image': open(img_path, 'rb')}
    url = api_url_path + '/classify'
    response = requests.post(url, files=files)
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.status_code)
        print(response.text)


# multiple images classification
def api_multiple_images(imgs_paths):
    files = [('images', open(img_path, 'rb')) for img_path in imgs_paths]
    url = api_url_path + '/classify-many'
    response = requests.post(url, files=files)
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.status_code)
        print(response.text)


def api_url(url):
    image_bytes = requests.get(url).content
    files = {'image': image_bytes}
    url = api_url_path + '/classify'
    response = requests.post(url, files=files)
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.status_code)
        print(response.text)


# test the api
print(f"images_path: {images_path}")
print(f"testing single image: {images_path[0]}")
api_single_image(images_path[0])
print(f"testing multiple images: {images_path}")
api_multiple_images(images_path)
```

## Deployment

1. install dependencies

```bash
pip install -r requirements.txt
```

2. start the api server

```bash
python main.py
```

## Configuration

See `config.yaml` for available configuration options.
