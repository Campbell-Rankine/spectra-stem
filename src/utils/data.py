import os
import multiprocessing
import numpy
from moviepy import AudioFileClip, VideoFileClip
import torch
import matplotlib.pyplot as plt


class AudioAttachment:
    def __init__(self, video_file: str, audio_file: str):
        assert os.path.exists(video_file) and os.path.exists(audio_file)
        self.video = VideoFileClip(video_file)
        self.audio = AudioFileClip(audio_file)
        self.output_path = video_file

    def attach(self):
        final_clip = self.video.set_audio(self.audio)

        # Export the final video with the new audio
        final_clip.write_videofile(self.output_path)


def plot_spectrogram(stft, title="Spectrogram"):
    magnitude = stft.abs()
    spectrogram = 20 * torch.log10(magnitude + 1e-8).cpu().numpy()
    _, axis = plt.subplots(1, 1)
    axis.imshow(
        spectrogram, cmap="viridis", vmin=-60, vmax=0, origin="lower", aspect="auto"
    )
    axis.set_title(title)
    plt.tight_layout()
