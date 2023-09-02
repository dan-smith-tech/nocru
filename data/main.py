from decouple import config
import multiprocessing
import numpy as np
import paramiko
import json
import cv2
import io

from data.gen import generate_image


class NpTypeEncoder(json.JSONEncoder):
    """
    Encoder override to convert numpy types to standard Python types for JSON serialization.
    """

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpTypeEncoder, self).default(obj)


class Generator(multiprocessing.Process):
    """
    Thread that generates a random image.
    """

    def __init__(self, thread_id, size, begin, directory):
        multiprocessing.Process.__init__(self)
        self.thread_id = thread_id
        self.size = size
        self.begin = begin
        self.directory = directory

    @staticmethod
    def generate_image(i):
        image, text_boxes = generate_image()

        label = {
            "id": i,
            "text_boxes": [box.__dict__ for box in text_boxes]
        }

        return image, label


class LocalGenerator(Generator):
    """
     Thread that generates a random image and stores it locally.
    """

    def __init__(self, thread_id, size, begin, directory):
        super().__init__(thread_id, size, begin, directory)

    def run(self):
        for i in range(self.begin, self.begin + self.size):
            image, label = self.generate_image(i)

            # store image locally
            image.save(self.directory + str(i) + ".png")

            # convert label object to JSON and store locally
            with open(self.directory + str(i) + '.json', 'w', encoding='utf-8') as f:
                json.dump(label, f, cls=NpTypeEncoder, ensure_ascii=False, indent=4)


class FTPGenerator(Generator):
    """
    Thread that generates a random image and stores it on a remote file system (via FTP).
    """

    def __init__(self, thread_id, size, begin, directory):
        super().__init__(thread_id, size, begin, directory)
        self.address = config("FILESYSTEM_ADDRESS")
        self.port = config("FILESYSTEM_PORT")
        self.username = config("FILESYSTEM_USERNAME")
        self.password = config("FILESYSTEM_PASSWORD")

    def run(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # security concerns
        ssh_client.connect(self.address, self.port, self.username, self.password)

        for i in range(self.begin, self.begin + self.size):
            image, label = self.generate_image(i)

            sftp = ssh_client.open_sftp()

            # convert Image to byte buffer
            _, image_buffer = cv2.imencode('.png', np.array(image))
            image_buffer_io = io.BytesIO(image_buffer)

            # convert label object to JSON
            label_json = json.dumps(label, cls=NpTypeEncoder, ensure_ascii=False, indent=4).encode()

            # convert json label to byte buffer
            label_json_buffer_io = io.BytesIO(label_json)

            # store files on remote file system
            sftp.putfo(image_buffer_io, self.directory + "/" + str(i) + ".png")
            sftp.putfo(label_json_buffer_io, self.directory + "/" + str(i) + ".json")

            # close IO buffers
            image_buffer_io.close()
            label_json_buffer_io.close()

            sftp.close()

        ssh_client.close()


def generate_dataset(generator, directory, size, begin, threads):
    """
    Generates a complete set of PNG images along with the relevant JSON label.

    :param size: Integer quantity of images to generate
    :param directory: String of subdirectory to store images in
    :param begin: Integer index to begin generating at
    :param threads: Integer quantity of threads to use
    :param generator: FTPGenerator or LocalGenerator depending on location of the dataset
    """

    extra = size % threads
    segment_size = (size - extra) // threads

    active_threads = []

    for i in range(threads - 1):
        active_threads.append(
            generator(str(i), segment_size, begin + i * segment_size, directory)
        )
    active_threads.append(
        generator(str(threads - 1), segment_size + extra, begin + (threads - 1) * segment_size, directory)
    )

    for thread in active_threads:
        thread.start()

    for thread in active_threads:
        thread.join()
