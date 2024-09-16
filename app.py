# Image Downsampler App

import os
import mimetypes
import logging
import io
from PIL import Image

# Increase Pillow max pixel support
Image.MAX_IMAGE_PIXELS = 209715200 # 200MB

# Constants
MAX_PIXEL_LENGTH = 10000
DPIS = [72, 300, 600, 1200]
MAX_TOTAL_BYTES = 10485760  # 10MB
SOURCE_DIR = "./tmp/source"
# SOURCE_DIR = "c:/dev/image-downsampler/tmp/source"

# Supported image formats based on MIME types
SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp']

# Set up logging
LOG_FILE = "image_resize.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def resize_image(image_path, dpi):
    try:
        # Open the image file
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            scale_factor = min(MAX_PIXEL_LENGTH / max(original_width, original_height), 1)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize image
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
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

        # Save the resized image
        resized_img.save(new_file_path, dpi=(dpi, dpi))
        logging.info(f"Image saved: {new_file_path}")
        
    except OSError as e:
        logging.error(f"Failed to save image {original_file_path} at {dpi}dpi: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error saving image {original_file_path} at {dpi}dpi: {str(e)}")


def check_image_size_in_memory(resized_img, dpi):
    try:
        # Use BytesIO to avoid writing to disk and check size in memory
        img_io = io.BytesIO()
        resized_img.save(img_io, format=resized_img.format, dpi=(dpi, dpi))
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
            if resized_img is None:
                continue  # Skip if resizing failed

            # Check if the resized image size in memory is below the max byte limit
            img_size = check_image_size_in_memory(resized_img, dpi)
            if img_size is not None and img_size > MAX_TOTAL_BYTES:
                # logging.warning(f"Image {file_name} at {dpi}dpi exceeds max size: {img_size} bytes (max {MAX_TOTAL_BYTES} bytes).")
                pass
            save_resized_image(resized_img, file_path, dpi)


if __name__ == "__main__":
    process_images()
