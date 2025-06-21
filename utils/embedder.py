from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pandas as pd
import numpy as np
import faiss

from utils.hyper_params import hyper_params

class Embedder:

    def __init__(self, data: pd.DataFrame, history: pd.DataFrame):
        self.model = SentenceTransformer("sentence-transformers/LaBSE")
        self.data = data
        self.history = history
        pass

    def _get_embedding(self, sentence):
        return self.model.encode(sentence)

    def _save_embds(self, save_path: str):
        '''
        Computes embeddings for messages and saves them to a file.
        '''
        batch_size = 512
        embeddings = []
        for idx in tqdm(range(0, len(self.data), batch_size), desc = "Computing gamefile embeddings!"):
            batch = list(self.data[idx:(idx + batch_size)])
            embds = self._get_embedding(batch)
            if idx == 0:
                embeddings = embds
            else:
                embeddings = np.concatenate([embeddings, embds], axis = 0)

        np.save(save_path, embeddings)

    def find_uniques(self, save_path: str):
        '''
        Finds the most out of norm messages based on the embeddings.
        '''
        try:
            embeddings = np.load(save_path)
        except:
            self._save_embds(save_path)
            embeddings = np.load(save_path)

        mean_sentence = np.mean(embeddings, axis = 0)
        indices = []
        idx = 0
        for embedding in embeddings:
            distance = np.linalg.norm(embedding - mean_sentence) 
            if distance > hyper_params["distance_threshold"]:
                indices.append(idx)
            idx += 1
        embeddings = embeddings[indices]
        np.save(hyper_params["processed_path"] + "/embeddings_shortlist.npy", embeddings)
        return indices

    def get_candidate_idxs(self, save_path: str):
        try:
            game_embeddings = np.load(save_path)
        except:
            raise Exception("Do not call this function before find_uniques!")

        candidates = []

            
        index = faiss.IndexFlatL2(game_embeddings.shape[1]) 
        index.add(game_embeddings)
        _, candidates = index.search(game_embeddings, k = hyper_params["k_similar"])

        return candidates








