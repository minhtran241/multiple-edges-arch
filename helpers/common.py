import os
from typing import List, Any, Union


def get_device_id(environ: Any) -> str:
    """
    Get the device ID from the environment variables.

    Args:
        environ (Any): The environment variables.

    Returns:
        str: The device ID.
    """
    return environ.get("HTTP_DEVICE_ID", None)


def partition_images(dir: str, num_parts: int) -> List[List[str]]:
    """
    Split the images in the directory into multiple parts for each edge node.

    Args:
        dir (str): The directory containing the images.
        num_parts (int): The number of edge nodes.

    Returns:
        List[List[str]]: A list of edge nodes, each containing a list of image paths.
    """
    # Get all image paths in the directory
    img_paths = [
        os.path.join(dir, img) for img in os.listdir(dir) if img.endswith(".jpg")
    ]
    # Split the image paths into num_parts parts
    data_parts = [[] for _ in range(num_parts)]
    for i, img_path in enumerate(img_paths):
        data_parts[i % num_parts].append(img_path)
    return data_parts


def image_to_bytes(filename: Union[str, bytes]) -> bytes:
    """
    Convert an image to bytes.

    Args:
        filename (str | bytes): The path to the image file or the image data in bytes.

    Returns:
        bytes: The image data in bytes.
    """
    with open(filename, "rb") as f:
        return f.read()


def bytes_to_image(data: bytes, save_path: str):
    """
    Convert bytes to an image and save it to a file.

    Args:
        data (bytes): The image data in bytes.
        save_path (str): The path to save the image.
    """
    with open(save_path, "wb") as f:
        f.write(data)


def partition_texts(dir: str, num_parts: int) -> List[List[str]]:
    """
    Partitions the text data in the specified directory into multiple parts based on the number of edge nodes.

    Args:
        dir (str): The directory containing the text data.
        num_parts (int): The number of parts to partition the data into.

    Returns:
        List[List[str]]: A list of partitions, where each partition contains a list of text data files.
    """
    text_files = [f for f in os.listdir(dir) if f.endswith(".txt")] * 300
    partitions = [[] for _ in range(num_parts)]
    for i, text_file in enumerate(text_files):
        partitions[i % num_parts].append(os.path.join(dir, text_file))
    return partitions


def partition_text(filename: str, num_parts: int) -> List[List[str]]:
    # Read a text file of reviews and split it into multiple parts for each edge node. Each reviews is a separate line in the file. 2 reviews are separated by one line
    with open(filename, "r") as f:
        reviews = f.readlines()
    data_parts = [[] for _ in range(num_parts)]
    for i, review in enumerate(reviews):
        data_parts[i % num_parts].append(review)
    return data_parts


def read_txt(filename: str) -> str:
    with open(filename, "r") as f:
        txt = f.read()
    return txt
