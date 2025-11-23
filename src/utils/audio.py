import io
import soundfile as sf
import numpy as np


def process_audio(stems, samplerate):
    # Handle stem audio collation
    outputs = []
    for name, audio in stems.items():
        wav_bytes = io.BytesIO()
        sf.write(wav_bytes, audio, samplerate, format="WAV")
        wav_bytes.seek(0)
        outputs.append((name, (samplerate, audio), wav_bytes))
    return outputs


def combine_stems(stems, selected, samplerate):
    # combine multiple tracks into a single track
    combined = np.zeros_like(next(iter(stems.values())))
    for stem in selected:
        combined += stems[stem]
    wav_bytes = io.BytesIO()
    sf.write(wav_bytes, combined, samplerate, format="WAV")
    wav_bytes.seek(0)
    return wav_bytes
