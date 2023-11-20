import argparse
import time
import os

import torchaudio
from pyannote.audio import Pipeline as DiarizePipe
torchaudio.set_audio_backend("sox_io")

OUT_FOLDER = "../data/diarized"

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", help="input file")
    args = argparser.parse_args()

    MODEL_ID = "pyannote/speaker-diarization-3.0"
    print(f"Loading pipeline for {MODEL_ID}")
    pipeline = DiarizePipe.from_pretrained(MODEL_ID)

    f = args.input
    print("Loading audio and diarizing...")
    waveform, sample_rate = torchaudio.load(f)
    start = time.time()
    diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})
    end = time.time()
    print(f"Done in {end - start:.2f} seconds")


    output_id = f.split("/")[-1].split(".")[0]
    os.makedirs(OUT_FOLDER, exist_ok=True)
    output_path = os.path.join(OUT_FOLDER, f"{output_id}.csv")
    print(f"Writing output to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start = turn.start
            end = turn.end
            f.write(f"{start:.1f},{end:.1f},speaker_{speaker}\n")
