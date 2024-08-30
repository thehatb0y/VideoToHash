```markdown
# Video Frame Hashing Script

This Python script takes a video, creates mosaics from every set number of frames, and then hashes each image in the mosaic.

## Installation

This script requires the following Python libraries:

- OpenCV (`cv2`)
- NumPy (`np`)
- Pillow (PIL Fork)
- imagehash
- threading

These libraries can be installed using pip:

```bash
pip install opencv-python numpy Pillow imagehash threading
```

**Use the code with caution.**

## Usage

1. Save this script as `main.py`.
2. Place the script in the same directory as your video file.
3. Run the script from the command line:

   ```bash
   python main.py
   ```

**Use the code with caution.**

## Note:

- This script uses multithreading to improve performance.
- The script will output various informational messages to the console, including:
  - Setup information (resolution, frames per image, etc.)
  - Total video frames
  - Estimated total images to be created
  - Time taken to process the video
  - Hashes for each image in the mosaics

## Script Breakdown

The script is broken down into several functions:

- **`create_image`**: Takes a list of frames, number of columns, output path, and an index (`p`) as arguments. It creates a horizontal mosaic from the frames, splits it vertically, and saves the final image.
  
- **`encode_frames`**: Takes the video path, output path, desired resolution, number of frames per image, and total video frame count as arguments. It reads the video frame-by-frame, resizes the frames, and adds them to a list. When the list reaches the number of frames per image, it creates a new thread to call `create_image` and then clears the list. This process continues until all frames have been processed.
  
- **`count_frames`**: Takes the video path as an argument and returns the total number of frames in the video.
  
- **`hashEverything`**: Takes the output path as an argument. It iterates through all image files in the output directory, opens them using Pillow, generates a perceptual hash using `imagehash`, prints the hash, and saves all hashes to a file named `hashList.txt`.
  
- **`main`**: This is the main function of the script. It defines various parameters such as maximum pixels, resolution, video paths, and calculates the number of frames per image and estimated total images. It then prints setup information, starts the time, calls `encode_frames`, stops the time, prints the elapsed time, and calls `hashEverything`.

## Customization

- You can modify the `MAX_PIXELS` variable to control the maximum number of pixels allowed in a single mosaic image.
- You can change the `W_res` and `H_res` variables to adjust the desired resolution of the resized frames.
- You can update the `in_video_path` variable to specify the path to your video file.
- You can modify the `out_video_path` variable to change the directory where the mosaic images and hash list will be saved.
```
