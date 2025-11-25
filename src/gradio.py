import gradio as gr
import os
from pydub import AudioSegment  # for combining stems


def ui():
    with gr.Blocks() as demo:
        gr.Markdown("### 🎶 Audio Stem Splitter")

        audio_input = gr.File(label="Upload Audio", file_types=[".wav", ".mp3"])

        # Fixed slots for 4 stems
        with gr.Row():
            vocals_audio = gr.Audio(label="Vocals", type="filepath")

        with gr.Row():
            drums_audio = gr.Audio(label="Drums", type="filepath")

        with gr.Row():
            bass_audio = gr.Audio(label="Bass", type="filepath")

        with gr.Row():
            other_audio = gr.Audio(label="Other", type="filepath")

        stem_selector = gr.CheckboxGroup(
            ["vocals", "drums", "bass", "other"], label="Select stems to combine"
        )
        combine_button = gr.Button("Combine Selected")
        combined_output = gr.File(label="Download Combined Stems")



        # ---- Stem splitting ----
        def on_submit(file):
            from src.stems import StemSplitter

            splitter = StemSplitter(load_on_init=True)

            labels, audios, files = splitter(file, output_path="./output")
            print(files, audios)
            del splitter

            # Map results back into fixed slots
            mapping = {
                "vocals": vocals_audio,
                "drums": drums_audio,
                "bass": bass_audio,
                "other": other_audio,
            }

            audio_vals = [None, None, None, None]

            for lbl, audio, _ in zip(labels, audios, files):
                if lbl in mapping:
                    idx = ["vocals", "drums", "bass", "other"].index(lbl)
                    audio_vals[idx] = audio

            return audio_vals

        audio_input.change(
            fn=on_submit,
            inputs=audio_input,
            outputs=[
                vocals_audio,
                drums_audio,
                bass_audio,
                other_audio,
            ],
        )

        # ---- Stem combining ----
        def combine_stems(file, selected):
            if not selected:
                return None

            combined = None
            for stem_name in selected:
                path = f"./output/{stem_name}.wav"
                if os.path.exists(path):
                    seg = AudioSegment.from_file(path)
                    if combined is None:
                        combined = seg
                    else:
                        combined = combined.overlay(seg)

            output_path = "./output/combined.wav"
            if combined:
                combined.export(output_path, format="wav")
                return output_path
            return None

        combine_button.click(
            combine_stems, inputs=[audio_input, stem_selector], outputs=combined_output
        )

    return demo