import cv2
import numpy as np
import time


def create_image(frames, num_columns, out_video_path, p):
    # Criar a imagem mosaico horizontal com os 1000 frames
    mosaic_horizontal = np.concatenate(frames, axis=1)
    # Dividir o mosaico horizontal em linhas para criar o mosaico vertical
    mosaic_vertical = np.array_split(mosaic_horizontal, num_columns, axis=1)
    mosaic_vertical = np.concatenate(mosaic_vertical, axis=0)
    # Salvar a imagem mosaico
    output_image_path = f'{out_video_path}/frames_mosaic_{p}.jpg'
    cv2.imwrite(output_image_path, mosaic_vertical)
    # Incrementar o valor de p para o próximo nome de imagem
    # Limpar a lista de frames para os próximos 1000 frames
    frames = []

def encode_frames(frames, video_path, out_video_path, W_res, H_res, imageCount):
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
        
        if len(frames) == int(imageCount):
            create_image(frames, num_columns, out_video_path, p)
            p = p + 1
            frames.clear()

    cap.release()
    
    # Se sobraram frames, criar a imagem mosaico com os frames restantes
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

def main():
    # Frame List
    frames = []
    # Max Pixels / Can't exceed 168956970 pixels
    #                           4294836225

    MAX_PIXELS = 168956970
    # Max Resolution
    W_res = 640#640
    H_res = 360#360
    # In Video Path
    in_video_path = 'BugBear.mp4'
    # Out Video Path
    out_video_path = 'BugBear'
    # How many frames fit into the image?
    imageCount = MAX_PIXELS / (W_res*H_res)
    countFrames = count_frames(in_video_path)
    
    print("\033[92mSetup\033[0m")
    print("\033[92mMax Pixels:\033[0m", "\033[91m", MAX_PIXELS, "\033[0m")
    print("\033[92mResolution Size:\033[0m", "\033[91m", W_res, "x", H_res, "\033[0m")
    print("\033[92mFrames per Image:\033[0m", "\033[91m", int(imageCount), "\033[0m")
    print("\033[92m", W_res, "x", H_res, "x", int(imageCount), "=\033[0m", "\033[91m", W_res*H_res*(int(imageCount)), "\033[0m")
    print("\033[92mIn Video Path:\033[0m", "\033[91m", in_video_path, "\033[0m")
    print("\033[92mOut Video Path:\033[0m", "\033[91m", out_video_path, "\033[0m")
    print("\033[92mTotal Video Frames:\033[0m", "\033[91m", countFrames, "\033[0m")
    print("\033[92mTotal Images:\033[0m", "\033[91m", countFrames / imageCount, "\033[0m")
    
    start = time.time()
    encode_frames(frames, in_video_path, out_video_path, W_res, H_res, imageCount)
    end = time.time()
    print("Time: ", end - start)

if __name__ == '__main__':
    main()