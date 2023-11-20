import argparse
from pathlib import Path
import json
import jax.numpy as jnp
from whisper_jax import FlaxWhisperPipline

class WhisperTranscriber:
    def __init__(self, model, out_dir, audio_file, language="no", batch_size=None, timestamps=True):
        self.model = model
        self.out_dir = out_dir
        self.audio_file = audio_file
        self.language = language
        self.batch_size = batch_size
        self.timestamps = timestamps

    def process(self):
        print(f"Loading model {self.model}")
        pipeline = FlaxWhisperPipline(self.model, dtype=jnp.bfloat16, batch_size=self.batch_size)

        print(f"Transcribing {self.audio_file}")
        transcript = pipeline(self.audio_file, task="transcribe", language=self.language, return_timestamps=self.timestamps)

        # save
        try:
            assert isinstance(transcript, dict) and ["text", "chunks"] == list(transcript.keys())
        except AssertionError:
            print("Transcript not in the correct format")
        filestem = Path(self.audio_file).stem
        outpath = Path(self.out_dir)
        jsonlpath = outpath / f"{filestem}.jsonl"
        with jsonlpath.open("w") as f:
            for line in transcript["chunks"]:
                json.dump(line, f, ensure_ascii=False)
                f.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio files with Jax Whisper")
    parser.add_argument("--model", type=str, help="Model to use", default="NbAiLab/nb-whisper-small-beta")
    parser.add_argument("-o", "--out_dir", type=str, help="Path to output directory")
    parser.add_argument("-a", "--audio_file", type=str, help="Path to audio file", required=True)
    parser.add_argument("-l", "--language", type=str, default="no", help="Language to use")
    parser.add_argument("-b", "--batch-size", type=int, default=None, help="Batch size")
    parser.add_argument("-t", "--timestamps", type=bool, default=True, help="Return timestamps")
    args = parser.parse_args()

    processor = WhisperTranscriber(args.model, args.out_dir, args.audio_file, args.language, args.batch_size, args.timestamps)
    processor.process()
