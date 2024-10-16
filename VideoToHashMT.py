import os
import threading
import cv2
import numpy as np
import time
import imagehash
import warnings
from PIL import Image
import concurrent.futures
import psutil
from collections import deque

warnings.simplefilter("ignore", Image.DecompressionBombWarning)
file_lock = threading.Lock()

# Otimização: Definir um número de workers baseado no número de núcleos do sistema
MAX_WORKERS = psutil.cpu_count(logical=False)

# Buffer para armazenar os frames durante o processamento
frame_buffer = deque()

def create_image_and_hash(frames, num_columns, out_video_path, p, escolha):
    """Cria o mosaico de imagens a partir dos frames e gera o hash imediatamente"""
    mosaic_horizontal = np.concatenate(frames, axis=1)
    mosaic_vertical = np.array_split(mosaic_horizontal, num_columns, axis=1)
    mosaic_vertical = np.concatenate(mosaic_vertical, axis=0)
    output_image_path = f'{out_video_path}/frames_mosaic_{p}.jpg'
    cv2.imwrite(output_image_path, mosaic_vertical)
    Image.MAX_IMAGE_PIXELS = None
    try:
        with Image.open(output_image_path) as img:
            if escolha == '1':
                img_hash = imagehash.phash(img)
            elif escolha == '2':
                img_hash = imagehash.average_hash(img)
            elif escolha == '3':
                img_hash = imagehash.dhash(img)
            else:
                print("Escolha inválida. Usando phash por padrão.")
                img_hash = imagehash.phash(img)

        # Escrever o hash no arquivo
        with file_lock:
            with open(f'{out_video_path}/hashListMT.txt', 'a') as f:
                f.write(f"{img_hash}\n")
    
    except Exception as e:
        print(f"Erro ao processar a imagem {output_image_path}: {e}")
    
    frames.clear()

def encode_frames(video_path, out_video_path, W_res, H_res, imageCount, escolha):
    """Processa frames do vídeo, cria mosaicos e gera hashes em paralelo"""
    num_columns = 20
    p = 0
    cap = cv2.VideoCapture(video_path)

    # Usar um buffer para gerenciar a leitura e processamento de frames
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_resized = cv2.resize(frame, (W_res, H_res))
            frame_buffer.append(frame_resized)

            # Quando o buffer atingir o tamanho máximo de frames permitidos por mosaico
            if len(frame_buffer) >= int(imageCount):
                deep_copy = list(frame_buffer)  # Copiar frames atuais
                frame_buffer.clear()  # Limpar o buffer para novos frames
                executor.submit(create_image_and_hash, deep_copy, num_columns, out_video_path, p, escolha)
                p += 1

        cap.release()

        # Processar os frames restantes no buffer
        if frame_buffer:
            executor.submit(create_image_and_hash, list(frame_buffer), num_columns, out_video_path, p, escolha)
            p += 1
            frame_buffer.clear()

    print(f"\033[92mReal Used Images:\033[0m \033[91m{p}\033[0m")

def count_frames(video_path):
    """Conta o número de frames em um vídeo"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total_frames

def main():
    MAX_PIXELS = 168956970
    W_res = 640
    H_res = 360
    in_video_path = 'videoplayback.mp4'
    out_video_path = 'playback'
    imageCount = MAX_PIXELS / (W_res * H_res)
    countFrames = count_frames(in_video_path)
    escolha = '1'  # Defina o método de hash, pode ser alterado conforme necessário

    print("\033[92mSetup\033[0m")
    print("\033[92mMax Pixels:\033[0m \033[91m", MAX_PIXELS, "\033[0m")
    print("\033[92mResolution Size:\033[0m \033[91m", W_res, "x", H_res, "\033[0m")
    print("\033[92mFrames per Image:\033[0m \033[91m", int(imageCount), "\033[0m")
    print("\033[92m", W_res, "x", H_res, "x", int(imageCount), "=\033[0m", "\033[91m", W_res * H_res * int(imageCount), "\033[0m")
    print("\033[92mIn Video Path:\033[0m \033[91m", in_video_path, "\033[0m")
    print("\033[92mOut Video Path:\033[0m \033[91m", out_video_path, "\033[0m")
    print("\033[92mTotal Video Frames:\033[0m \033[91m", countFrames, "\033[0m")
    print("\033[92mTotal Images:\033[0m \033[91m", countFrames / imageCount, "\033[0m")

    start = time.time()
    encode_frames(in_video_path, out_video_path, W_res, H_res, imageCount, escolha)
    end = time.time()
    print("\033[92mElapsed Time:\033[0m \033[91m", end - start, "\033[0m")

if __name__ == '__main__':
    main()





    

