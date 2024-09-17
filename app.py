# Image Downsampler App

import os
import mimetypes
import logging
import io
from PIL import Image

# Increase Pillow max pixel support
Image.MAX_IMAGE_PIXELS = 209715200  # 200MB

# Constants
MAX_PIXEL_LENGTH = 10000
MIN_PIXEL_LENGTH = 600
DPIS = [72, 300, 600, 1200]
MAX_TOTAL_BYTES = 10485760  # 10MB
SOURCE_DIR = "./tmp/source"
RESAMPLING_FILTER = Image.LANCZOS
JPEG_QUALITY = 95

# Supported image formats based on MIME types
SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp']

# Set up logging
LOG_FILE = "image_resize.log"

def init_logger():
    delete_file_if_exists(LOG_FILE)
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def delete_file_if_exists(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        logging.warning(f"Error deleting file {file_path}: {e}")


def resize_image(image_path, dpi):
    try:
        # Open the image file
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            
            # Assume the highest DPI as the base for scaling
            # TODO - read DPI from source image
            original_dpi = max(DPIS)

            # Calculate scale factor based on DPI
            dpi_scale_factor = dpi / original_dpi

            # Apply both DPI and pixel length scaling
            new_width = int(original_width * dpi_scale_factor)
            new_height = int(original_height * dpi_scale_factor)

            # Determine the scale factor based on the longest edge
            scale_factor = min(MAX_PIXEL_LENGTH / max(new_width, new_height), 1)
            
            # Ensure the longest edge is between MAX_PIXEL_LENGTH and MIN_PIXEL_LENGTH, inclusive
            # new_width = max(int(new_width * scale_factor), MIN_PIXEL_LENGTH)
            # new_height = max(int(new_height * scale_factor), MIN_PIXEL_LENGTH)

            # Resize image using the resampling filter
            resized_img = img.resize((new_width, new_height), RESAMPLING_FILTER)
            return resized_img

    except IOError as e:
        logging.error(f"Failed to open image {image_path}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error resizing image {image_path}: {str(e)}")
        return None


def save_resized_image(resized_img, original_file_path, dpi):
    try:
        file_name, file_ext = os.path.splitext(os.path.basename(original_file_path))
        target_dir = f"{SOURCE_DIR}_images_{dpi}dpi"
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        new_file_name = f"{file_name}_{dpi}dpi{file_ext}"
        new_file_path = os.path.join(target_dir, new_file_name)

        # Save the resized image with quality settings for JPEG
        save_params = {'dpi': (dpi, dpi)}
        if file_ext.lower() in ['.jpg', '.jpeg']:
            save_params['quality'] = JPEG_QUALITY
        
        resized_img.save(new_file_path, **save_params)
        logging.info(f"Image saved: {new_file_path}")
        
    except OSError as e:
        logging.error(f"Failed to save image {original_file_path} at {dpi}dpi: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error saving image {original_file_path} at {dpi}dpi: {str(e)}")


def check_image_size_in_memory(resized_img, dpi):
    try:
        # Use BytesIO to avoid writing to disk and check size in memory
        img_io = io.BytesIO()
        save_params = {'dpi': (dpi, dpi), 'quality': JPEG_QUALITY}
        # if resized_img.format.lower() in ['jpeg', 'jpg']:
            # save_params['quality'] = JPEG_QUALITY
        resized_img.save(img_io, format=resized_img.format, **save_params)
        img_size = img_io.tell()
        return img_size
    except Exception as e:
        logging.error(f"Error checking image size in memory for {dpi}dpi: {str(e)}")
        return None


def process_images():    
    for file_name in os.listdir(SOURCE_DIR):
        file_path = os.path.join(SOURCE_DIR, file_name)

        # Verify that it's an image file using MIME types
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type not in SUPPORTED_FORMATS:
            logging.info(f"Skipped non-image file: {file_path}")
            continue

        logging.info(f"Processing image: {file_name}")

        for dpi in DPIS:
            resized_img = resize_image(file_path, dpi)
            # if resized_img is None:
            #     continue  # Skip if resizing failed

            # Check if the resized image size in memory is above the max byte limit
            # img_size = check_image_size_in_memory(resized_img, dpi)
            # if img_size is not None and img_size > MAX_TOTAL_BYTES:
            #     logging.warning(f"Image {file_name} at {dpi}dpi exceeds max size: {img_size} bytes (max {MAX_TOTAL_BYTES} bytes).")
            
            # Save the resized image regardless of size
            save_resized_image(resized_img, file_path, dpi)


if __name__ == "__main__":
    init_logger()
    process_images()
