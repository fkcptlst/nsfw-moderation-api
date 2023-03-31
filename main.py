from typing import List, Dict

import yaml
from addict import Dict as Addict
import uvicorn
from fastapi import FastAPI, File, UploadFile
from nsfw_detector import predict

from util import Cache, CacheDB, CacheImagesContextManager, load_images

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    config = Addict(config)

cache_db = CacheDB(config.cache.db)
cache = Cache(cache_db, cache_dir=config.cache.folder, expire=eval(config.cache.expiry))
# 3600 * 24 * 7

model = predict.load_model(f'./model/{config.model.name}')

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello from NSFW Detector"}


async def get_results(images: List[UploadFile] = File(...)):
    with CacheImagesContextManager(cache, images) as (original_names, image_paths, cached_results, hash_strs):
        results: List[Dict[str, float]] = []  # dict[original_name, result]
        input_image_paths = []
        for i, cached_result in enumerate(cached_results):
            if cached_result is not None:  # already in cache
                # cached_result:str, convert str to dict
                results.append(eval(cached_result))
            else:
                results.append({original_names[i]: {}})
                input_image_paths.append(image_paths[i])  # only predict images not in cache

        if len(input_image_paths) > 0:  # at least one image not in cache
            images_ndarray, paths = load_images(input_image_paths)
            probs = predict.classify_nd(model, images_ndarray)

            pred_ptr = 0  # pointer to the images not in cache
            probs_ptr = 0  # pointer to the predicted result
            for i in range(len(results)):
                if list(results[i].values()) == [{}]:  # not in cache, predict
                    if paths[pred_ptr] is None:  # failed to load image
                        results[i] = {original_names[i]: {}}  # empty dict
                    else:
                        results[i] = {original_names[i]: probs[probs_ptr]}  # predict result
                        probs_ptr += 1
                    pred_ptr += 1

        # update cache
        for i in range(len(results)):
            cache.update_result(hash_strs[i], str(results[i]))

        return results


@app.post("/classify")
async def classify(image: UploadFile = File(...)):
    results = await get_results([image])
    return results[0]


@app.post("/classify-many")
async def classify_many(images: List[UploadFile] = File(...)):
    return await get_results(images)


if __name__ == "__main__":
    uvicorn.run(app,
                host=config.web.host,
                port=config.web.port,
                log_level=config.web.log_level,
                workers=config.web.workers)
