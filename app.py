# Image Downsampler App

import os
import mimetypes
from PIL import Image

# Constants
MAX_PIXEL_LENGTH = 10000
DPIS = [72, 300, 600, 1200]
MAX_TOTAL_BYTES = 10485760  # 10MB
SOURCE_DIR = "./tmp/source"
# SOURCE_DIR = "c:/dev/image-downsampler/tmp/source"

# Supported image formats based on MIME types
SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp']

# Increase Pillow max pixel support
Image.MAX_IMAGE_PIXELS = 209715200 # 200MB

def resize_image(image_path, dpi):
    # Open the image file
    with Image.open(image_path) as img:
        # Calculate the new size
        original_width, original_height = img.size
        scale_factor = min(MAX_PIXEL_LENGTH / max(original_width, original_height), 1)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize image
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        return resized_img

def save_resized_image(resized_img, original_file_path, dpi):
    # Get original filename and extension
    file_name, file_ext = os.path.splitext(os.path.basename(original_file_path))
    
    # Create the target directory if it doesn't exist
    target_dir = f"{SOURCE_DIR}_images_{dpi}dpi"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Create new filename with dpi suffix
    new_file_name = f"{file_name}_{dpi}dpi{file_ext}"
    new_file_path = os.path.join(target_dir, new_file_name)
    
    # Save the resized image
    resized_img.save(new_file_path, dpi=(dpi, dpi))

def process_images():
    # Iterate over all files in the source directory
    for file_name in os.listdir(SOURCE_DIR):
        file_path = os.path.join(SOURCE_DIR, file_name)
        
        # Verify that it's an image file using MIME types
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type not in SUPPORTED_FORMATS:
            print(f"Skipping non-image file: {file_name} : {mime_type}")
            continue  # Skip non-image files
        
        # Resize and save for each DPI
        for dpi in DPIS:
            resized_img = resize_image(file_path, dpi)
            
            # Ensure the resized image doesn't exceed the max total bytes
            temp_file_path = os.path.join(SOURCE_DIR, f"temp_{dpi}dpi.jpg")
            resized_img.save(temp_file_path, dpi=(dpi, dpi))
            
            # if os.path.getsize(temp_file_path) > MAX_TOTAL_BYTES:
            #     print(f"Skipping file due to exceeding max total bytes: {file_name} : {os.path.getsize(temp_file_path)}")
            # else:
            save_resized_image(resized_img, file_path, dpi)

            os.remove(temp_file_path)  # Clean up temporary file
            
            print(f"Processed image: {file_name} @ {dpi}dpi")

        print(f"Finished processing image: {file_name}")

if __name__ == "__main__":
    process_images()
