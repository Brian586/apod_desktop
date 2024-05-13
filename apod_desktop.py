""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py [apod_date]

Parameters:
  apod_date = APOD date (format: YYYY-MM-DD)
"""
from datetime import date, timedelta
import os
import re
import hashlib
import sqlite3
import apod_api
import image_lib

# Full paths of the image cache folder and database
# - The image cache directory is a subdirectory of the specified parent directory.
# - The image cache database is a sqlite database located in the image cache directory.
script_dir = os.path.dirname(os.path.abspath(__file__))
image_cache_dir = os.path.join(script_dir, 'images')
image_cache_db = os.path.join(image_cache_dir, 'image_cache.db')


def main():
    ## DO NOT CHANGE THIS FUNCTION ##
    # Get the APOD date from the command line
    apod_date = get_apod_date()    

    # Initialize the image cache
    init_apod_cache()

    # Add the APOD for the specified date to the cache
    apod_id = add_apod_to_cache(apod_date)

    # Get the information for the APOD from the DB
    apod_info = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:
        image_lib.set_desktop_background_image(apod_info['file_path'])


def get_apod_date():
    """Gets the APOD date
     
    The APOD date is taken from the first command line parameter.
    Validates that the command line parameter specifies a valid APOD date.
    Prints an error message and exits script if the date is invalid.
    Uses today's date if no date is provided on the command line.

    Returns:
        date: APOD date
    """
    import sys

    # Get the APOD date from the command line argument
    if len(sys.argv) > 1:
        apod_date_str = sys.argv[1]
    else:
        apod_date_str = date.today().isoformat()

    try:
        apod_date = date.fromisoformat(apod_date_str)
    except ValueError:
        print(f"Error: Invalid date format: '{apod_date_str}'")
        sys.exit(1)

    # Validate the APOD date
    first_apod_date = date(1995, 6, 16)
    if apod_date < first_apod_date:
        print(f"Error: APOD date cannot be before {first_apod_date.isoformat()}")
        sys.exit(1)
    elif apod_date > date.today():
        print("Error: APOD date cannot be in the future")
        sys.exit(1)

    return apod_date


def init_apod_cache():
    """Initializes the image cache by:
    - Creating the image cache directory if it does not already exist,
    - Creating the image cache database if it does not already exist.
    """
    # Create the image cache directory if it does not already exist
    os.makedirs(image_cache_dir, exist_ok=True)

    # Create the DB if it does not already exist
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apod_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            explanation TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def add_apod_to_cache(apod_date):
    """Adds the APOD image from a specified date to the image cache.
     
    The APOD information and image file is downloaded from the NASA API.
    If the APOD is not already in the DB, the image file is saved to the 
    image cache and the APOD information is added to the image cache DB.

    Args:
        apod_date (date): Date of the APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if a new APOD is added to the
        cache successfully or if the APOD already exists in the cache. Zero, if unsuccessful.
    """
    print(f"APOD date: {apod_date.isoformat()}")

    # Download the APOD information from the NASA API
    apod_info = apod_api.get_apod_info(apod_date)
    if apod_info is None:
        print("Error: Failed to retrieve APOD information from NASA API")
        return 0

    print(f"APOD title: {apod_info['title']}")

    # Download the APOD image
    image_url = apod_api.get_apod_image_url(apod_info)
    image_data = image_lib.download_image(image_url)
    if image_data is None:
        print("Error: Failed to download APOD image")
        return 0

    # Calculate the SHA-256 hash of the image
    sha256 = hashlib.sha256(image_data).hexdigest()
    print(f"APOD SHA-256: {sha256}")

    # Check whether the APOD already exists in the image cache
    apod_id = get_apod_id_from_db(sha256)
    if apod_id != 0:
        print("APOD image is already in cache.")
        return apod_id

    # Save the APOD file to the image cache directory
    file_path = determine_apod_file_path(apod_info['title'], image_url)
    print(f"APOD file path: {file_path}")
    if image_lib.save_image_file(image_data, file_path):
        print(f"Saving image file as {file_path}...success")
    else:
        print(f"Error: Failed to save image file as {file_path}")
        return 0

    # Add the APOD information to the DB
    apod_id = add_apod_to_db(apod_info['title'], apod_info['explanation'], file_path, sha256)
    if apod_id != 0:
        print("Adding APOD to image cache DB...success")
    else:
        print("Error: Failed to add APOD to image cache DB")

    return apod_id


def add_apod_to_db(title, explanation, file_path, sha256):
    """Adds specified APOD information to the image cache DB.
     
    Args:
        title (str): Title of the APOD image
        explanation (str): Explanation of the APOD image
        file_path (str): Full path of the APOD image file
        sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: The ID of the newly inserted APOD record, if successful. Zero, if unsuccessful       
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO apod_images (title, explanation, file_path, sha256)
            VALUES (?, ?, ?, ?)
        """, (title, explanation, file_path, sha256))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print("Error: APOD image already exists in the database")
        return 0
    finally:
        conn.close()


def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache having a specified SHA-256 hash value
    
    This function can be used to determine whether a specific image exists in the cache.

    Args:
        image_sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if it exists. Zero, if it does not.
    """
    # TODO: Complete function body
    return 0


def determine_apod_file_path(image_title, image_url):
    """Determines the path at which a newly downloaded APOD image must be 
    saved in the image cache. 
    
    The image file name is constructed as follows:
    - The file extension is taken from the image URL
    - The file name is taken from the image title, where:
        - Leading and trailing spaces are removed
        - Inner spaces are replaced with underscores
        - Characters other than letters, numbers, and underscores are removed

    For example, suppose:
    - The image cache directory path is 'C:\\temp\\APOD'
    - The image URL is 'https://apod.nasa.gov/apod/image/2205/NGC3521LRGBHaAPOD-20.jpg'
    - The image title is ' NGC #3521: Galaxy in a Bubble '

    The image path will be 'C:\\temp\\APOD\\NGC_3521_Galaxy_in_a_Bubble.jpg'

    Args:
        image_title (str): APOD title
        image_url (str): APOD image URL
    
    Returns:
        str: Full path at which the APOD image file must be saved in the image cache directory
    """
    # Remove leading and trailing spaces from the title
    image_title = image_title.strip()

    # Replace inner spaces with underscores and remove non-word characters
    filename = re.sub(r'\W+', '_', image_title)

    # Get the file extension from the image URL
    _, ext = os.path.splitext(image_url)

    # Construct the full image file path
    file_path = os.path.join(image_cache_dir, f"{filename}{ext}")

    return file_path


def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD having a specified
    ID from the DB.

    Args:
        image_id (int): ID of APOD in the DB

    Returns:
        dict: Dictionary of APOD information
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT title, explanation, file_path FROM apod_images WHERE id = ?
        """, (image_id,))
        result = cursor.fetchone()
        if result:
            title, explanation, file_path = result
            apod_info = {
                'title': title,
                'explanation': explanation,
                'file_path': file_path
            }
            return apod_info
        else:
            return None
    finally:
        conn.close()


def get_all_apod_titles():
    """Gets a list of the titles of all APODs in the image cache

    Returns:
        list: Titles of all images in the cache
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT title FROM apod_images")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


if __name__ == '__main__':
    main()