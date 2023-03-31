import hashlib
from typing import List
from pathlib import Path
import time

from fastapi import File, UploadFile

from .CacheDB import CacheDB

"""
Table: Cache
| id | hash_str(index) | expiry_time | path | created_at | updated_at | deleted_at | result |
"""


class Cache:
    def __init__(self, cache_db: CacheDB, cache_dir: str = './cache', expire: int = 3600 * 24 * 7):
        self.cache_db = cache_db
        self.cache_dir = cache_dir
        self.expire = expire
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def update_expiry_time(self, new_expiry_time: int):
        """
        Update the expiry time of the cache, and delete all expired cache
        :param new_expiry_time:
        :return:
        """
        self.expire = new_expiry_time
        not_expired = self.cache_db.select_all_not_expired()
        for cache in not_expired:
            self.cache_db.update(
                hash_str=cache['hash_str'],
                expiry_time=cache['updated_at'] + self.expire,
                path=cache['path'],
                created_at=cache['created_at'],
                updated_at=cache['updated_at'],
                deleted_at=cache['deleted_at'],
                result=cache['result'])

        self.delete_expire()

    def delete_expire(self):
        """
        delete all expired cache
        :return:
        """
        newly_expired = self.cache_db.select_all_newly_expired()
        for cache in newly_expired:
            Path(cache['path']).unlink()  # delete the file or link
        self.cache_db.delete_all_expired()

    def update_result(self, hash_str: str, result: str):
        """
        update the result of the cache
        :param hash_str:
        :param result:
        :return:
        """
        cache = self.cache_db.select(hash_str)
        self.cache_db.update(
            hash_str=cache['hash_str'],
            expiry_time=int(time.time() + self.expire),  # LRU
            path=cache['path'],
            created_at=cache['created_at'],
            updated_at=cache['updated_at'],
            deleted_at=cache['deleted_at'],
            result=result)

    def cache(self, images: List[UploadFile] = File(...)):
        """
        function cache here is a verb, not a noun
        1. check if the image is in cache
            a. if not in cache, save the image and insert into cache_db
            b. if in cache, check if it is deleted
                i. if deleted, save the image and update cache_db
                ii. if not deleted, do nothing
        :param images:
        :return: original names, paths, cached results, hash_strs
        """
        image_names: List[str] = [image.filename for image in images]
        image_paths: List[str] = []
        cached_results: List[str | None] = []
        hash_strs: List[str] = []
        for image in images:
            # img_bytes = await image.read()
            img_bytes = image.file.read()
            hash_str = hashlib.md5(img_bytes).hexdigest()
            hash_strs.append(hash_str)
            cache = self.cache_db.select(hash_str)
            image_path = Path(f'{self.cache_dir}/{hash_str}.{image.filename}')
            if cache is None:  # not in cache, new
                # save the image
                with open(image_path, 'wb') as f:
                    f.write(img_bytes)
                # insert into cache_db
                self.cache_db.insert(hash_str, int(time.time()) + self.expire, str(image_path), "{}")
                cached_results.append(None)
            elif cache['deleted_at'] is not None:  # deleted
                image_path = Path(cache['path']) if cache['path'] \
                    else Path(f'{self.cache_dir}/{hash_str}.{image.filename}')
                # save the image
                with open(image_path, 'wb') as f:
                    f.write(img_bytes)
                # update cache_db
                self.cache_db.update(
                    hash_str=hash_str,
                    created_at=cache['created_at'],
                    updated_at=int(time.time()),
                    deleted_at=None,
                    path=str(image_path),
                    expiry_time=int(time.time()) + self.expire,
                    result="{}")
                cached_results.append(None)
            else:  # already cached
                cached_results.append(cache['result'])
            image_paths.append(str(image_path))
        return image_names, image_paths, cached_results, hash_strs


class CacheImagesContextManager:
    """
    Context manager for caching images
    """

    def __init__(self, cache: Cache, images: List[UploadFile] = File(...)):
        self.cache = cache
        self.images = images

    def __enter__(self):
        """
        :return: original names, cached paths, cached results, hash_strs
        """
        return self.cache.cache(self.images)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cache.delete_expire()
