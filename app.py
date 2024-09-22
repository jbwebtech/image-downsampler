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
JPEG_QUALITY = 98
DEFAULT_DPI = 300

# Feature Flags
ENABLE_CHECK_MAX_BYTES = True
ENABLE_CHECK_MIN_MAX_LENGTH = True
ENABLE_JPEG_QUALITY = True

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

# Helper function to split file name and extension
def split_file_name(file_path):
    return os.path.splitext(os.path.basename(file_path))

def get_original_dpi(image):
    """Extract the original DPI from the image metadata. Default to DEFAULT_DPI if not found."""
    dpi = (DEFAULT_DPI, DEFAULT_DPI)
    try:
        dpi = image.info.get('dpi')  # Default to 72 DPI if not found
    except Exception as e:
        logging.warning(f"Failed to read DPI from source image metadata: {e}")    
    return max(dpi)  # Return the higher value for scaling

def resize_image(image_path, dpi):
    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            original_dpi = get_original_dpi(img)
            
            if dpi > original_dpi:
                logging.info(f"Skipping image {image_path} at {dpi}dpi (original DPI: {original_dpi})")
                return None

            dpi_scale_factor = dpi / original_dpi

            if original_width > original_height:  #  Landscape
                new_width = int(original_width * dpi_scale_factor)
                new_height = int(new_width * (original_height / original_width))
            else:  #  Portrait or square
                new_height = int(original_height * dpi_scale_factor)
                new_width = int(new_height * (original_width / original_height))

            if ENABLE_CHECK_MIN_MAX_LENGTH:
                # Resize the image if its longest side is longer than MAX_PIXEL_LENGTH or shorter than MIN_PIXEL_LENGTH
                scale_factor = min(MAX_PIXEL_LENGTH / max(new_width, new_height), 1)
                new_width = max(int(new_width * scale_factor), MIN_PIXEL_LENGTH)
                new_height = max(int(new_height * scale_factor), MIN_PIXEL_LENGTH)

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
        # Split file name and extension using the helper function
        file_name, file_ext = split_file_name(original_file_path)
        target_dir = f"{SOURCE_DIR}_images_{dpi}dpi"
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        new_file_name = f"{file_name}_{dpi}dpi{file_ext}"
        new_file_path = os.path.join(target_dir, new_file_name)

        save_params = {'dpi': (dpi, dpi)}
        if ENABLE_JPEG_QUALITY and file_ext.lower() in ['.jpg', '.jpeg']:
            save_params['quality'] = JPEG_QUALITY
        
        resized_img.save(new_file_path, **save_params)
        logging.info(f"Image saved: {new_file_path}")
        
    except OSError as e:
        logging.error(f"Failed to save image {original_file_path} at {dpi}dpi: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error saving image {original_file_path} at {dpi}dpi: {str(e)}")

# Updated check_image_size_in_memory function without file_name parameter
def check_image_size_in_memory(resized_img, original_file_path, dpi):
    try:
        # Split file name and extension using the helper function
        _, file_ext = split_file_name(original_file_path)

        # Determine the correct image format for saving in memory
        img_io = io.BytesIO()
        save_params = {'dpi': (dpi, dpi)}
        if ENABLE_JPEG_QUALITY and file_ext.lower() in ['.jpg', '.jpeg']:
            save_params['quality'] = JPEG_QUALITY

        # Ensure the correct image format is passed when saving
        image_format = file_ext.lstrip('.').upper()  # Convert extension to format

        if image_format == 'JPG':
            image_format = 'JPEG'

        resized_img.save(img_io, format=image_format, **save_params)
        img_size = img_io.tell()
        return img_size
    except Exception as e:
        logging.error(f"Error checking image size in memory for {original_file_path} at {dpi}dpi: {str(e)}")
        return None

def process_images():
    for file_name in os.listdir(SOURCE_DIR):
        file_path = os.path.join(SOURCE_DIR, file_name)

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type not in SUPPORTED_FORMATS:
            logging.info(f"Skipped non-image file: {file_path}")
            continue

        logging.info(f"Processing image: {file_name}")

        for dpi in DPIS:
            resized_img = resize_image(file_path, dpi)
            if resized_img is None:
                continue

            if ENABLE_CHECK_MAX_BYTES:
                img_size = check_image_size_in_memory(resized_img, file_path, dpi)
                if img_size is not None and img_size > MAX_TOTAL_BYTES:
                    logging.warning(f"Image {file_name} at {dpi}dpi exceeds max size: {img_size} bytes (max {MAX_TOTAL_BYTES} bytes).")
            
            save_resized_image(resized_img, file_path, dpi)

if __name__ == "__main__":
    init_logger()
    process_images()
