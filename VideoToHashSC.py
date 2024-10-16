import cv2
import numpy as np
import time
import imagehash
import os
from PIL import Image
import psutil  # Adicionando o psutil para coletar as métricas de CPU

def create_image(frames, num_columns, out_video_path, p):
    # Criar a imagem mosaico horizontal com os 1000 frames
    mosaic_horizontal = np.concatenate(frames, axis=1)
    # Dividir o mosaico horizontal em linhas para criar o mosaico vertical
    mosaic_vertical = np.array_split(mosaic_horizontal, num_columns, axis=1)
    mosaic_vertical = np.concatenate(mosaic_vertical, axis=0)
    # Salvar a imagem mosaico
    output_image_path = f'{out_video_path}/frames_mosaic_{p}.jpg'
    cv2.imwrite(output_image_path, mosaic_vertical)
    frames = []

def encode_frames(frames, video_path, out_video_path, W_res, H_res, imageCount, cpu_usage):
    num_columns = 20
    p = 0
    cap = cv2.VideoCapture(video_path)
    # Ler todos os frames do vídeo
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_resized = cv2.resize(frame, (W_res, H_res))  # Reduzir para a resolução desejada
        frames.append(frame_resized)
        
        # Coletar o uso de CPU a cada frame processado
        cpu_usage.append(psutil.cpu_percent(interval=None))

        if len(frames) == int(imageCount):
            create_image(frames, num_columns, out_video_path, p)
            p = p + 1
            frames.clear()

    cap.release()
    
    if frames != []:
        create_image(frames, num_columns, out_video_path, p)
        p = p + 1
        frames.clear()
            
    print("Total Images: ", p)

def count_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total_frames

def hashEverything(out_video_path):
    formatos_de_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    imagens = []
    for arquivo in os.listdir(out_video_path):
        if any(arquivo.endswith(extensao) for extensao in formatos_de_imagem):
            caminho_completo = os.path.join(out_video_path, arquivo)
            imagem = Image.open(caminho_completo)
            imagens.append(imagem)

    escolha = '1'
    heshList = []
    
    for imagem in imagens:
        if escolha == '1':
            img = imagehash.phash(imagem)
        elif escolha == '2':
            img = imagehash.average_hash(imagem)
        elif escolha == '3':
            img = imagehash.dhash(imagem)
        else:
            print("Escolha inválida. Usando phash por padrão.")
            img = imagehash.phash(imagem)
        
        heshList.append(img)
        print(img)

    with open(f'{out_video_path}/hashList.txt', 'w') as f:
        for item in heshList:
            f.write("%s\n" % item)

def main():
    frames = []
    MAX_PIXELS = 168956970
    W_res = 640
    H_res = 360
    in_video_path = 'videoplayback.mp4'
    out_video_path = 'playback'
    imageCount = MAX_PIXELS / (W_res*H_res)
    countFrames = count_frames(in_video_path)
    
    print("\033[92mSetup\033[0m")
    print("\033[92mMax Pixels:\033[0m", "\033[91m", MAX_PIXELS, "\033[0m")
    print("\033[92mResolution Size:\033[0m", "\033[91m", W_res, "x", H_res, "\033[0m")
    print("\033[92mFrames per Image:\033[0m", "\033[91m", int(imageCount), "\033[0m")
    print("\033[92mIn Video Path:\033[0m", "\033[91m", in_video_path, "\033[0m")
    print("\033[92mOut Video Path:\033[0m", "\033[91m", out_video_path, "\033[0m")
    print("\033[92mTotal Video Frames:\033[0m", "\033[91m", countFrames, "\033[0m")
    print("\033[92mTotal Images:\033[0m", "\033[91m", countFrames / imageCount, "\033[0m")
    
    start = time.time()
    cpu_usage = []  # Lista para armazenar o uso de CPU
    encode_frames(frames, in_video_path, out_video_path, W_res, H_res, imageCount, cpu_usage)
    hashEverything(out_video_path)
    end = time.time()

    # Calcular a média de uso de CPU
    avg_cpu_usage = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
    print(f"Média de uso do CPU durante a execução: {avg_cpu_usage:.2f}%")
    print("Time: ", end - start)

if __name__ == '__main__':
    main()
