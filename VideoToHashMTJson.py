import os
import cv2
import numpy as np
import imagehash
import json
import threading
import concurrent.futures
import psutil
import time
from PIL import Image
from collections import deque
import warnings

MAX_WORKERS = psutil.cpu_count(logical=False)
file_lock = threading.Lock()
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

# Buffer para armazenar os frames durante o processamento
frame_buffer = deque()

hashes = []

def create_image_and_hash(frames, num_columns, out_video_path, p, escolha, hashes):
    mosaic_horizontal = np.concatenate(frames, axis=1)
    mosaic_vertical = np.array_split(mosaic_horizontal, num_columns, axis=1)
    mosaic_vertical = np.concatenate(mosaic_vertical, axis=0)
    output_image_path = f'{out_video_path}/frames_mosaic_{p}.jpg'
    cv2.imwrite(output_image_path, mosaic_vertical)

    try:
        with Image.open(output_image_path) as img:
            hash_pointer = str(imagehash.phash(Image.fromarray(frames[0])))

            if escolha == '1':
                img_hash = str(imagehash.phash(img))
            elif escolha == '2':
                img_hash = str(imagehash.average_hash(img))
            elif escolha == '3':
                img_hash = str(imagehash.dhash(img))
            else:
                img_hash = str(imagehash.phash(img))

            hashes.append({"HashPointer": hash_pointer, "Hash": img_hash})

    except Exception as e:
        print(f"Erro ao processar a imagem {output_image_path}: {e}")

    frames.clear()

def encode_frames(video_path, out_video_path, W_res, H_res, imageCount, escolha, hashes):
    num_columns = 20
    p = 0
    cap = cv2.VideoCapture(video_path)

    frame_buffer = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_resized = cv2.resize(frame, (W_res, H_res))
            frame_buffer.append(frame_resized)

            if len(frame_buffer) >= int(imageCount):
                deep_copy = list(frame_buffer)
                frame_buffer.clear()
                executor.submit(create_image_and_hash, deep_copy, num_columns,
                                out_video_path, p, escolha, hashes)
                p += 1

        cap.release()

        if frame_buffer:
            executor.submit(create_image_and_hash, list(frame_buffer), num_columns,
                            out_video_path, p, escolha, hashes)
            p += 1
            frame_buffer.clear()

    resultado = {
        "Max Pixels": W_res * H_res * int(imageCount),
        "Resolution Size": f"{W_res} x {H_res}",
        "Frames per Image": int(imageCount),
        "Calculation": f"{W_res} x {H_res} x {int(imageCount)} = {W_res * H_res * int(imageCount)}",
        "Total Video Frames": count_frames(video_path),
        "Total Blocks": p,
        "Hashes": hashes
    }

    with open(f'{out_video_path}/resultado.json', 'w') as json_file:
        json.dump(resultado, json_file, indent=4)

def count_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total_frames

def main():
    MAX_PIXELS = 168956970
    W_res = 640
    H_res = 360
    in_video_path = 'Temple_Ruins_Bandtis_pirate.mp4'
    out_video_path = 'playback'
    escolha = '1'

    imageCount = MAX_PIXELS / (W_res * H_res)
    countFrames = count_frames(in_video_path)

    print("\033[92mSetup\033[0m")
    print("\033[92mMax Pixels:\033[0m \033[91m", MAX_PIXELS, "\033[0m")
    print("\033[92mResolution Size:\033[0m \033[91m", W_res, "x", H_res, "\033[0m")
    print("\033[92mFrames per Image:\033[0m \033[91m", int(imageCount), "\033[0m")
    print("\033[92m", W_res, "x", H_res, "x", int(imageCount), "=\033[0m", "\033[91m", W_res * H_res * int(imageCount), "\033[0m")
    print("\033[92mIn Video Path:\033[0m \033[91m", in_video_path, "\033[0m")
    print("\033[92mOut Video Path:\033[0m \033[91m", out_video_path, "\033[0m")
    print("\033[92mTotal Video Frames:\033[0m \033[91m", countFrames, "\033[0m")
    print("\033[92mTotal Images:\033[0m \033[91m", countFrames / imageCount, "\033[0m")

    hashes = []
    start = time.time()
    encode_frames(in_video_path, out_video_path, W_res,
                  H_res, imageCount, escolha, hashes)
    end = time.time()
    print("\033[92mElapsed Time:\033[0m \033[91m", end - start, "\033[0m")

if __name__ == '__main__':
    main()
