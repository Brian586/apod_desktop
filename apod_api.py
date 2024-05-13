'''
Library for interacting with NASA's Astronomy Picture of the Day API.
'''
from datetime import date

import requests

# NASA API endpoint and your API key
NASA_API_URL = "https://api.nasa.gov/planetary/apod"
NASA_API_KEY = ""


def main():
    # Test get_apod_info()
    apod_date = date(2024, 4, 16)  # Replace with the desired date
    apod_info = get_apod_info(apod_date)

    if apod_info:
        print("APOD information for", apod_date.isoformat())
        print("Title:", apod_info["title"])
        print("Explanation:", apod_info["explanation"])
        print("Media Type:", apod_info["media_type"])

        # Test get_apod_image_url()
        image_url = get_apod_image_url(apod_info)
        if image_url:
            print("Image URL:", image_url)
        else:
            print("No image URL found.")
    else:
        print(f"Failed to retrieve APOD information for {apod_date.isoformat()}")


def get_apod_info(apod_date):
    """Gets information from the NASA API for the Astronomy
    Picture of the Day (APOD) from a specified date.

    Args:
        apod_date (date): APOD date (Can also be a string formatted as YYYY-MM-DD)

    Returns:
        dict: Dictionary of APOD info, if successful. None if unsuccessful
    """

    params = {
        "date": apod_date.isoformat(),
        "api_key": NASA_API_KEY,
        "thumbs": True  # Include thumbnail URL for videos
    }

    try:
        response = requests.get(NASA_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def get_apod_image_url(apod_info_dict):
    """Gets the URL of the APOD image from the dictionary of APOD information.

    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.

    Args:
        apod_info_dict (dict): Dictionary of APOD info from API

    Returns:
        str: APOD image URL
    """
    media_type = apod_info_dict["media_type"]
    if media_type == "image":
        return apod_info_dict["hdurl"]
    elif media_type == "video":
        return apod_info_dict["thumbnail_url"]
    else:
        return None


if __name__ == '__main__':
    main()