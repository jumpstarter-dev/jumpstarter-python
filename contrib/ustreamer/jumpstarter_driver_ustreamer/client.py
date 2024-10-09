import io
import logging
from base64 import b64decode

import imagehash
from PIL import Image

from jumpstarter.client import DriverClient

from .common import UStreamerState

log = logging.getLogger("ustreamer")

class UStreamerClient(DriverClient):
    """UStreamer client class

    Client methods for the UStreamer driver.
    """

    def state(self):
        """
        Get state of ustreamer service
        """

        return UStreamerState.model_validate(self.call("state"))

    def snapshot(self):
        """
        Get a snapshot image from the video input

        :return: JPEG image data
        :rtype: bytes
        """
        return b64decode(self.call("snapshot"))

    def write_snapshot(self, filename):
        """
        Write a snapshot image into a disk file

        :param str filename: file name to write the snapshot image
        """
        with open(filename, "wb") as f:
            f.write(self.snapshot())

    def hash_snapshot(self, hash_func=imagehash.average_hash, hash_size=8):
        """
        Get a hash of the snapshot image through the imagehash library

        :param hash_func: hash function from imagehash library
        :type hash_func: function
        :param hash_size: hash size for the hash function
        :type hash_size: int
        :return: hash of the snapshot image
        :rtype: ImageHash
        """
        input_jpg_data = self.snapshot()
        input_img = Image.open(io.BytesIO(input_jpg_data))
        return hash_func(input_img, hash_size=hash_size)

    def assert_snapshot(self, reference_img_file, tolerance=1, hash_func=imagehash.average_hash, hash_size=8):
        """
        Assert the snapshot image is the same as the reference image

        :param str reference_img_file: reference image file name
        :param int tolerance: hash difference tolerance
        :param hash_func: hash function from imagehash library
        :type hash_func: function
        :param hash_size: hash size for the hash function
        :type hash_size: int

        :raises AssertionError: if the snapshot image is different from the reference image
        """
        diff, snapshot_data  = self._snapshot_diff(reference_img_file, hash_func, hash_size)
        if diff > tolerance:
            save_filename = "FAILED_"+reference_img_file
            log.error(f"Image hashes are different, saving the actual image as {save_filename}")
            with open(save_filename, "wb") as f:
                f.write(snapshot_data)
            raise AssertionError(f"{self.name}.assert_snapshot {reference_img_file}:"
                                 " diff {diff} > tolerance {tolerance}")

    def _snapshot_diff(self, reference_img_file, hash_func=imagehash.average_hash, hash_size=8):
        snapshot_data = self.snapshot()
        snapshot_img = Image.open(io.BytesIO(snapshot_data))
        ref_hash = hash_func(Image.open(reference_img_file), hash_size=hash_size)
        snapshot_hash = hash_func(snapshot_img, hash_size=hash_size)
        diff = ref_hash - snapshot_hash
        log.info(f"{self.name} comparing snapshot {reference_img_file}:"
                 " snapshot {snapshot_hash}, ref {ref_hash}, diff: {diff}")
        return diff, snapshot_data
