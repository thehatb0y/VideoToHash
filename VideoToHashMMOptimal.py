import os
import cv2
import numpy as np
import time
import warnings
from PIL import Image
import imagehash

from dask.distributed import Client

# Ignorar avisos de decompression bomb do PIL
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

def create_image_and_hash_dask(start_frame, end_frame, num_columns, temp_dir, p, video_path, W_res, H_res):
    """
    Cria a imagem mosaico localmente, gera o pHash, apaga a imagem mosaico e retorna o hash.

    Parâmetros:
    - start_frame: Frame inicial para processamento.
    - end_frame: Frame final para processamento.
    - num_columns: Número de colunas no mosaico.
    - temp_dir: Diretório temporário local para salvar o mosaico.
    - p: Índice da parte atual.
    - video_path: Caminho do vídeo de entrada.
    - W_res: Largura da resolução para redimensionamento.
    - H_res: Altura da resolução para redimensionamento.

    Retorna:
    - pHash da imagem mosaico como string.
    """
    # Garantir que o diretório temporário exista no worker
    os.makedirs(temp_dir, exist_ok=True)

    # Abrir o vídeo
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frames = []
    
    # Ler os frames especificados
    for _ in range(end_frame - start_frame):
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (W_res, H_res))
        frames.append(frame_resized)
    cap.release()

    if not frames:
        return None

    # Criar a imagem mosaico horizontal
    mosaic_horizontal = np.concatenate(frames, axis=1)
    # Dividir o mosaico horizontal em colunas para criar o mosaico vertical
    mosaic_vertical = np.array_split(mosaic_horizontal, num_columns, axis=1)
    mosaic_vertical = np.concatenate(mosaic_vertical, axis=0)

    # Salvar a imagem mosaico localmente
    mosaic_filename = f'frames_mosaic_{p}.jpg'
    output_image_path = os.path.join(temp_dir, mosaic_filename)
    success = cv2.imwrite(output_image_path, mosaic_vertical)

    if not success:
        print(f"Erro ao salvar o mosaico: {output_image_path}")
        return None

    # Abrir a imagem com PIL para calcular o pHash
    try:
        imagem = Image.open(output_image_path)
        img_hash = imagehash.phash(imagem)
        imagem.close()
    except Exception as e:
        print(f"Erro ao calcular pHash para {output_image_path}: {e}")
        return None

    # Apagar a imagem mosaico
    try:
        os.remove(output_image_path)
    except OSError as e:
        print(f"Erro ao apagar o mosaico {output_image_path}: {e}")

    return str(img_hash)

def encode_frames(video_path, out_video_path, W_res, H_res, imageCount, client, temp_dir):
    """
    Divide os frames do vídeo em partes, cria mosaicos, calcula os pHashes e salva os hashes.

    Parâmetros:
    - video_path: Caminho do vídeo de entrada.
    - out_video_path: Caminho da pasta compartilhada para salvar o hashList.txt.
    - W_res: Largura da resolução para redimensionamento.
    - H_res: Altura da resolução para redimensionamento.
    - imageCount: Número de frames por mosaico.
    - client: Cliente Dask para submissão de tarefas.
    - temp_dir: Diretório temporário local para salvar mosaicos.
    """
    # Obter o número total de frames
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    num_columns = 20
    p = 0
    tasks = []
    frames_per_task = int(imageCount)
    start_frame = 0
    while start_frame < total_frames:
        end_frame = min(start_frame + frames_per_task, total_frames)
        # Enviar a tarefa para o Dask
        future = client.submit(
            create_image_and_hash_dask,
            start_frame,
            end_frame,
            num_columns,
            temp_dir,
            p,
            video_path,
            W_res,
            H_res
        )
        tasks.append(future)
        p += 1
        start_frame = end_frame

    # Aguardar todas as tarefas serem concluídas e coletar os hashes
    hashes = client.gather(tasks)

    # Filtrar possíveis None (caso alguma tarefa não gerou frames ou houve erro)
    hashes = [h for h in hashes if h is not None]
    
    print("\033[92mTotal de Mosaicos Processados:\033[0m", "\033[91m", len(hashes), "\033[0m")
    
    # Salvar os hashes em um arquivo txt na pasta compartilhada
    hash_list_path = os.path.join(out_video_path, 'hashList.txt')
    try:
        with open(hash_list_path, 'w') as f:
            for img_hash in hashes:
                f.write(f"{img_hash}\n")
        print(f"Lista de hashes salva em {hash_list_path}")
    except Exception as e:
        print(f"Erro ao salvar hashList.txt: {e}")

def count_frames(video_path):
    """
    Conta o número total de frames no vídeo.

    Parâmetros:
    - video_path: Caminho do vídeo.

    Retorna:
    - Número total de frames.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Erro ao abrir o vídeo: {video_path}")
        return 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total_frames

def main():
    """
    Função principal que configura o ambiente, inicia o processamento e gera os hashes.
    """
    # Substitua '192.168.0.104' pelo IP real do scheduler
    client = Client('tcp://192.168.0.104:8786')

    # Resolução máxima para redimensionamento dos frames
    W_res = 640
    H_res = 360
    # Caminho do vídeo de entrada
    in_video_path = '/mnt/comp/videoplayback.mp4'
    # Caminho da pasta compartilhada para salvar o hashList.txt
    out_video_path = '/mnt/comp'
    # Diretório temporário local para salvar mosaicos
    temp_dir = '/tmp/mosaics'
    # Máximo de pixels para o mosaico
    MAX_PIXELS = 168956970
    # Quantidade de frames que cabem na imagem mosaico
    imageCount = MAX_PIXELS / (W_res * H_res)
    # Contar o número total de frames no vídeo
    countFrames = count_frames(in_video_path)

    # Exibir informações de configuração
    print("\033[92mSetup\033[0m")
    print("\033[92mMax Pixels:\033[0m", "\033[91m", MAX_PIXELS, "\033[0m")
    print("\033[92mResolution Size:\033[0m", "\033[91m", W_res, "x", H_res, "\033[0m")
    print("\033[92mFrames per Image:\033[0m", "\033[91m", int(imageCount), "\033[0m")
    print("\033[92m", W_res, "x", H_res, "x", int(imageCount), "=\033[0m", "\033[91m", W_res * H_res * int(imageCount), "\033[0m")
    print("\033[92mIn Video Path:\033[0m", "\033[91m", in_video_path, "\033[0m")
    print("\033[92mOut Video Path:\033[0m", "\033[91m", out_video_path, "\033[0m")
    print("\033[92mTotal Video Frames:\033[0m", "\033[91m", countFrames, "\033[0m")
    print("\033[92mTotal Images:\033[0m", "\033[91m", countFrames / imageCount, "\033[0m")

    start = time.time()
    encode_frames(in_video_path, out_video_path, W_res, H_res, imageCount, client, temp_dir)
    end = time.time()
    print("\033[92mElapsed Time:\033[0m", "\033[91m", end - start, "\033[0m")

if __name__ == '__main__':
    main()
