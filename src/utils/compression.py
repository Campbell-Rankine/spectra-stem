import pyflac
import numpy as np
import soundfile as sf
from pathlib import Path
import queue


class Passthrough:

    def __init__(self, args):
        self.idx = 0
        self.total_bytes = 0
        self.queue = queue.SimpleQueue()

        info = sf.info(str(args.input_file))
        if info.subtype == "PCM_16":
            dtype = "int16"
        elif info.subtype == "PCM_32":
            dtype = "int32"
        else:
            raise ValueError(
                f"WAV input data type must be either PCM_16 or PCM_32: Got {info.subtype}"
            )

        self.data, self.sr = sf.read(args.input_file, dtype=dtype, always_2d=True)

        self.encoder = pyflac.StreamEncoder(
            write_callback=self.encoder_callback,
            sample_rate=self.sr,
            blocksize=args.block_size,
        )

        self.decoder = pyflac.StreamDecoder(write_callback=self.decoder_callback)

    def encode(self):
        self.encoder.process(self.data)
        self.encoder.finish()

    def decode(self):
        while not self.queue.empty():
            self.decoder.process(self.queue.get())
        self.decoder.finish()

    def encoder_callback(
        self, buffer: bytes, num_bytes: int, num_samples: int, current_frame: int
    ):
        self.total_bytes += num_bytes
        self.queue.put(buffer)

    def decoder_callback(
        self, data: np.ndarray, sample_rate: int, num_channels: int, num_samples: int
    ):
        assert self.sr == sample_rate
        assert np.array_equal(data, self.data[self.idx : self.idx + num_samples])
        self.idx += num_samples
