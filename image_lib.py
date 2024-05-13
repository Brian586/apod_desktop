'''
Library of useful functions for working with images.
'''
import os
import requests
import ctypes


def main():
    # Test download_image()
    image_url = "https://apod.nasa.gov/apod/image/2303/FlamingStarComet_Roell_7504.jpg"
    image_data = download_image(image_url)

    if image_data:
        print(f"Downloaded {len(image_data)} bytes from {image_url}")

        # Test save_image_file()
        test_image_path = "test_image.jpg"
        if save_image_file(image_data, test_image_path):
            print(f"Saved image to {test_image_path}")

            # Test set_desktop_background_image()
            if set_desktop_background_image(test_image_path):
                print("Set desktop background image successfully")
            else:
                print("Failed to set desktop background image")
        else:
            print("Failed to save image file")
    else:
        print(f"Failed to download image from {image_url}")

    # Test scale_image()
    original_size = (3000, 2000)
    scaled_size = scale_image(original_size)
    print(f"Scaled image size: {scaled_size}")


def download_image(image_url):
    """Downloads an image from a specified URL.

    DOES NOT SAVE THE IMAGE FILE TO DISK.

    Args:
        image_url (str): URL of image

    Returns:
        bytes: Binary image data, if successful. None, if unsuccessful.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def save_image_file(image_data, image_path):
    """Saves image data as a file on disk.

    DOES NOT DOWNLOAD THE IMAGE.

    Args:
        image_data (bytes): Binary image data
        image_path (str): Path to save image file

    Returns:
        bool: True, if successful. False, if unsuccessful
    """
    try:
        with open(image_path, "wb") as f:
            f.write(image_data)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def set_desktop_background_image(image_path):
    """Sets the desktop background image to a specific image.

    Args:
        image_path (str): Path of image file

    Returns:
        bool: True, if succcessful. False, if unsuccessful
    """
    try:
        # Get the absolute path of the image file and convert it to a Unicode string
        image_path_unicode = str(os.path.abspath(image_path))
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path_unicode, 0)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def scale_image(image_size, max_size=(800, 600)):
    """Calculates the dimensions of an image scaled to a maximum width
    and/or height while maintaining the aspect ratio  

    Args:
        image_size (tuple[int, int]): Original image size in pixels (width, height) 
        max_size (tuple[int, int], optional): Maximum image size in pixels (width, height). Defaults to (800, 600).

    Returns:
        tuple[int, int]: Scaled image size in pixels (width, height)
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    # NOTE: This function is only needed to support the APOD viewer GUI
    resize_ratio = min(max_size[0] / image_size[0], max_size[1] / image_size[1])
    new_size = (int(image_size[0] * resize_ratio), int(image_size[1] * resize_ratio))
    return new_size


if __name__ == '__main__':
    main()