import jsonlines
import argparse
import re
from tqdm import tqdm

import pandas as pd
import numpy as np
from faiss import Index
from autofaiss import build_index

from typing import Tuple


def rnd(num):
    return round(num * 2) / 2

def get_df(tv_show):
    base_path = "../data"
    speaker_path = f"{base_path}/diarized/{tv_show}.csv"

    def rnd(num):
        return round(num * 2) / 2

    df = pd.read_csv(speaker_path, header=None)
    df.columns = ["start", "end", "speaker"]
    # keep only start and speaker. rename start to "time"
    df = df[["start", "speaker"]]
    df = df.rename(columns={"start": "time"})
    df["time"] = df["time"].apply(rnd)

    def transform_speaker(speaker_str):
        return int(speaker_str.split("_")[2])

    df["speaker"] = df["speaker"].apply(transform_speaker)

    # TRANSCRIPTIONS
    transcr_path = f"{base_path}/transcriptions/{tv_show}.jsonl"
    parsed = []
    with jsonlines.open(transcr_path) as reader:
        for obj in reader:
            timestamp = obj["timestamp"]
            txt = obj["text"]
            start, end = timestamp
            parsed.append({"time": rnd(start), "text": txt})

    transcript_df = pd.DataFrame(parsed)
    transcript_df["text"] = transcript_df["text"].apply(lambda x: x.strip())

    pattern = re.compile(r"\d+(?:,\d+)+")
    def filter_start(sent):
        sent = pattern.sub("", sent)
        return re.sub(r"^[^a-zA-Z0-9]+", "", sent)

    transcript_df["text"] = transcript_df["text"].apply(filter_start)


    for index, row in transcript_df.iterrows():
        time = row["time"]
        text = row["text"]
        closest = df.iloc[(df["time"]-time).abs().argsort()[:1]]
        closest_speaker = closest["speaker"].values[0]
        transcript_df.at[index, "speaker"] = closest_speaker

    return transcript_df


def get_index_and_data(model, tv_show) -> Tuple[Index, pd.DataFrame]:
    """
    model: SentenceTransformer model
    """
    # parsed = []
    # print("Reading data")
    # with jsonlines.open(tv_show) as reader:
    #     for obj in reader:
    #         timestamp = obj["timestamp"]
    #         txt = obj["text"]
    #         start, end = timestamp
    #         parsed.append({"start": start, "end": end, "text": txt})
    # df = pd.DataFrame(parsed)
    df = get_df(tv_show)
    print("Encoding data")
    texts = list(set(df["text"].tolist()))
    embs = model.encode(texts, show_progress_bar=True)
    
    # create a mapping between text and embeddings
    text_to_emb = {}
    for text, emb in zip(texts, embs):
        text_to_emb[text] = emb
    text_to_emb[""] = model.encode([""])[0]

    embeddings = []
    for index, row in df.iterrows():
        text = row["text"]
        embeddings.append(text_to_emb[text])
    embeddings = np.array(embeddings).astype("float32")
    
    print("Building index")
    index, _ = build_index(embeddings, save_on_disk=False, verbose=0)
    print("Success")

    return index, df
