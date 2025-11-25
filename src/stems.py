import torch as T
import torch.nn as nn
import torchaudio
import os
from typing import Optional, Iterable, Callable
from abc import ABC, abstractmethod
from copy import deepcopy
import logging
import gradio as gr

from src.utils.io import get_song_name, mkdir_if_not_exist
from src.utils.chunking import separate_sources
from src.utils.data import plot_spectrogram


class _BaseStemSplitter(ABC):
    def __init__(self, bundle, load_on_init: bool, logger=None, **kw):
        self.bundle = bundle
        self.model = None
        self.device = T.device(
            kw.get("device", "cuda:0" if T.cuda.is_available() else "cpu")
        )
        self.dtype = kw.get("dtype", T.double)
        self.logger = logger
        self.needs_scaling = False

        if load_on_init:
            self.load()

        self.to(self.device, dtype=self.dtype)

    @property
    def sources(self) -> list:
        if hasattr(self.model, "sources"):
            return list(self.model.sources)
        else:
            raise ValueError(
                f"Unable to load sources list from type: {type(self.model)}"
            )

    def set_logger(self, logger: logging.Logger):
        self.logger = logger

    def log(self, msg: str, level="info"):
        if not self.logger is None:
            self.logger.__getattribute__(level)(msg)
        else:
            print(f"Level={level} : {msg}")

    def to(self, device: str, dtype=None):
        # iterate over class objects, if they have device set device
        for name, attr in self.__dict__.items():
            if hasattr(attr, "device") or hasattr(attr, "to"):
                self.__getattribute__(name).to(device)
                if not dtype is None:
                    self.__getattribute__(name).to(dtype=dtype)

    def load(self, force=False):
        if force or not self.model is None:
            assert hasattr(self.bundle, "get_model")
            self.model = self.bundle.get_model()
            self.sample_rate = self.bundle.sample_rate

    def normalize_waveform(self, waveform: T.Tensor) -> T.Tensor:
        self.needs_scaling = True
        mu = waveform.mean(0)
        normalized = (waveform - mu.mean()) / mu.std()
        self.log(f"Before Normalization - max: {waveform.max()}, min: {waveform.min()}")
        return normalized

    def unnormalize_waveform(self, waveform: T.Tensor) -> T.Tensor:
        self.needs_scaling = False
        mu = waveform.mean(0)
        unnormalized = (waveform * mu.std()) + mu.mean()
        self.log(f"Unnormalized - max: {unnormalized.max()}, min: {unnormalized.min()}")
        return unnormalized

    def load_audio(self, path: str, normalize: Optional[bool] = True) -> tuple:
        # kw = tensor kwargs
        assert os.path.exists(path)

        waveform, audio_sr = torchaudio.load(path)
        if not audio_sr == self.sample_rate:
            raise ValueError(
                f"Sample rate for song={audio_sr} does not match model sample rate={self.sample_rate}"
            )

        mix = deepcopy(waveform)
        if normalize:
            waveform = self.normalize_waveform(waveform)

        waveform.to(self.device, dtype=self.dtype)
        mix.to(self.device, dtype=self.dtype)

        return (audio_sr, waveform, mix)

    @abstractmethod
    def build(self) -> tuple:
        pass

    @abstractmethod
    def forward(self, *args, **kwargs):
        assert not self.model is None


class StemSplitter(_BaseStemSplitter):
    def __init__(
        self,
        bundle: Optional[str] = torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS,
        load_on_init: Optional[bool] = False,
        segment: Optional[int] = 10,
        overlap: Optional[float] = 0.1,
        n_fft: Optional[int] = 4096,
        n_hop: Optional[int] = 4,
        audio_chunking: Optional[Callable] = separate_sources,
        plotting_fn: Optional[Callable] = plot_spectrogram,
        output_reader: Optional[type] = gr.Audio,
        **kw,
    ):
        super().__init__(bundle, load_on_init, **kw)

        # model params
        self.segment = segment
        self.overlap = overlap
        self.n_fft = n_fft
        self.n_hop = n_hop

        # cls functions
        self.audio_chunking = audio_chunking
        self._plotter = plotting_fn
        self.__output_reader = output_reader

        if load_on_init:
            self.load(True)

    def build(self, path: str, **kw) -> tuple:
        # build model dataset
        self.log(f"Building dataset from {path}")

        audio_sr, waveform, mix = self.load_audio(path, kw.get("normalize", True))
        self.log(
            f"Found audio: sample rate={audio_sr} waveform shape={waveform.shape}, normalize_waveform={kw.get('normalize', True)}"
        )
        return audio_sr, waveform, mix

    def _grad_forward(self, waveform, mix):
        assert not self.model is None and hasattr(self, "sample_rate")
        self.to(self.device, self.dtype)
        # split audio into iterable chunks with overlap / fade in / fade out
        sources = self.audio_chunking(
            self.model,
            waveform[None],
            self.sample_rate,
            device=self.device,
            segment=self.segment,
            overlap=self.overlap,
        )[0]
        if self.needs_scaling:
            sources = self.unnormalize_waveform(sources)

        audios = dict(zip(self.sources, sources))
        return audios, waveform, mix

    def _no_grad_forward(self, waveform, mix):
        # split audio into iterable chunks with overlap / fade in / fade out
        with T.no_grad():
            return self._grad_forward(waveform, mix)

    def forward(self, waveform, mix, no_grad=True):
        if no_grad:
            return self._no_grad_forward(waveform, mix)
        return self._grad_forward(waveform, mix)

    def __call__(
        self,
        path_to_audio: str,
        output_path: Optional[str] = None,
        no_cache: Optional[bool] = False,
        return_original: Optional[bool] = False,
    ):
        assert os.path.exists(path_to_audio)
        samplerate, waveform, mix = self.build(path_to_audio)
        audios, _, _ = self.forward(waveform, mix, no_grad=True)

        file_paths = []
        if not output_path is None:
            song_name = get_song_name(path_to_audio)
            for k, v in audios.items():
                ext = "mono" if v.shape[0] == 1 else "stereo"
                mkdir_if_not_exist(output_path, subdirs=[song_name])
                file_paths.append(f"{output_path}/{song_name}/{k}.wav")
                torchaudio.save(
                    f"{output_path}/{song_name}/{k}.wav",
                    v.cpu(),
                    self.sample_rate,
                )
                self.log(
                    f"Saved song to: {output_path}/{song_name}/{k}.wav | Audio min={v.min()}, Audio Max={v.max()}"
                )
        _audios = []
        for f in file_paths:
            _audios.append(self.__output_reader(f))

        return (
            list(audios.keys()),
            _audios,
            file_paths,
        )