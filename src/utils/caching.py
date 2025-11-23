import os
import torchaudio
import numpy as np
import gradio as gr
from pathlib import Path

from src.utils.compression import Passthrough


def cache_stem_request(
    path_to_audio: str, output_path: str, compress=True, **compression_kw
) -> tuple[int, np.ndarray]:
    """
    Caching handler for the StemSplitter class. Compression = wave -> FLAC
    """
    song_name = path_to_audio.split("/")[-1].split(".")[0]
    audios = []
    files = []

    # ui cacheing
    if os.path.exists(f"{output_path}/{song_name}"):
        for file in os.listdir(f"{output_path}/{song_name}"):
            wav = gr.Audio(f"{output_path}/{song_name}/{file}")
            audios.append(wav)
            files.append(f"{output_path}/{song_name}/{file}")
            # handle wave -> FLAC
            if compress:
                compressor = Passthrough(Path(f"{output_path}/{song_name}/{file}"))
                compressor.encode()

    return audios, files
