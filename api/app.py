import flask
from flask_cors import CORS
import os
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from create_index import get_index_and_data
import numpy as np

app = flask.Flask(__name__)
CORS(app)

FRONTEND_HOST = "localhost"
FRONTEND_PORT = 3000
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080

app.config['CORS_HEADERS'] = 'Content-Type'


SBERT_MODEL = "NbAiLab/nb-sbert-base"
# SBERT_MODEL = "intfloat/multilingual-e5-base"


class DataStore:
    def __init__(self):
        print(f"Loading s-bert model")
        self.model = SentenceTransformer(SBERT_MODEL)
        self.index: faiss.Index = None
        self.df: pd.DataFrame = None
        self.speaker_df: pd.DataFrame = None
        self.last_timestamp = 0

        self.data_folder = "../data/transcriptions/"
        self.valid_transcriptions = [
            f.split(".")[0] for f in os.listdir(self.data_folder) if f.endswith(".jsonl")
        ]

    @staticmethod
    def transform_speaker(speaker_str):
        return int(speaker_str.split("_")[2])
    
    def update(self, tv_show):
        self.index, self.df = get_index_and_data(self.model, tv_show)
        print(self.df.head())
        
    # a function to retrieve the corresponding subtitle from a current timestamp (start)
    # the df has the following columns: start, end, text
    def get_subtitle(self, timestamp, buffer=5):
        if self.df is None:
            return None
        
        subtitle = self.df[(self.df['time'] <= timestamp) & (self.df['time'].shift(-1) > timestamp)]
        if not subtitle.empty:
            speaker = subtitle.iloc[0]['speaker']
            speaker = int(float(speaker))
            text = subtitle.iloc[0]['text']
            return f"({speaker}) {text}"
        else:
            return "..."
        
        # # round timestamp to nearest 0.5 second
        # timestamp = round(timestamp * 2) / 2
        # current_row = self.df[self.df["time"] == timestamp]
        # speaker = current_row["speaker"].values[0]
        # text = current_row["text"].values[0]

        # return f"({speaker}) {text}"
        
    def query(self, q, k=1):
        emb = self.model.encode([q], show_progress_bar=False)
        dists, matches = self.index.search(emb, k)
        print(dists)
        print(matches)
        # print top 4 matches
        for match in matches[0]:
            print(self.df.iloc[match]["time"])
            print(self.df.iloc[match]["text"])
        
        res = self.df.iloc[matches[0]]
        return [
            {"time": row["time"]}
            for _, row in res.iterrows()
        ]

datastore = DataStore()

@app.route('/status')
def health_check() -> str:
    return f"app is running on {SERVER_HOST}:{SERVER_PORT}"

@app.route('/update', methods=['POST'])
def update() -> flask.Response:
    tv_show = flask.request.json.get('path')
    datastore.update(tv_show)
    return flask.jsonify({"status": "ok"})

@app.route('/transcriptions')
def get_valid() -> flask.Response:
    return flask.jsonify(datastore.valid_transcriptions)

@app.route('/search', methods=['POST'])
def predictions() -> flask.Response:
    text = flask.request.json.get('text')
    k = flask.request.json.get('k')
    print(text)
    query_result = datastore.query(q=text, k=k)
    print("result", query_result)
    return flask.jsonify(query_result)

@app.route('/subtitle', methods=['POST'])
def get_subtitle() -> flask.Response:
    timestamp = flask.request.json.get('timestamp')
    print(f"timestamp: {timestamp}")
    subtitle = datastore.get_subtitle(timestamp)
    return flask.jsonify({"text": subtitle})

app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True, threaded=True)

