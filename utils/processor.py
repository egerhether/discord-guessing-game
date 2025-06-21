import pandas as pd
import numpy as np 
import glob
import time
from utils.embedder import Embedder
from utils.hyper_params import hyper_params

class Processor:

    def __init__(self, data_path: str):
        files = glob.iglob(data_path + "/*.csv") 
        if not files:
            raise Exception(f"Create {data_path} directory and put exported message files there!")
        self.game_msgs = pd.DataFrame()
        self.history = pd.DataFrame()
        self.indices = None
        self.weights = {}
        start = time.time()
        print("Reading discord csv files")
        for file in files:
            msg = pd.read_csv(file)
            self.history = pd.concat([self.history, msg])
        print(f"Discord files read. ({time.time() - start}s)")


    def _cleanup(self):
        '''
        Performs basic cleanup with removing corrupted rows.
        Nothing more as we want full history to be retained.
        '''
        self.history = self.history[["Author", "Date", "Content", "Reactions"]] # take these columsn
        self.history = self.history.dropna(subset=["Content", "Author", "Date"], how="any", inplace=False) 
        self.history = self.history[self.history["Author"].isin(hyper_params["users_to_include"])]
    
    def _cleanup2(self):
        '''
        More thorough cleanup preparing for creating game-ready
        message set.
        '''
        self.df = self.history
        self.df = self.df[~self.df["Content"].str.contains("http")] # remove links
        self.df = self.df[~self.df["Content"].str.contains("@")] # remove tags
        self.df = self.df[~self.df["Content"].str.count(" ").lt(2)] # remove msgs with less than 3 words
        self.df = self.df[~self.df["Content"].str.count(" ").gt(9)] # remove msgs with more than 10 words
        self.df = self.df[~self.df["Content"].str.contains("Joined the server.")]
        self.df = self.df[~self.df["Content"].str.contains("Pinned a message.")]
        self.df.index = np.arange(len(self.df))
        self.embedder = Embedder(self.df["Content"], self.history["Content"])

    def _get_unique(self):
        '''
        Uses Embedder class to choose unique messages to guess.
        '''
        try:
            self.indices = self.embedder.find_uniques(hyper_params["processed_path"] + "/embeddings.npy")
        except:
            raise Exception("Do not run this function before _cleanup2()!")

    def _compute_weights(self):
        
        num_occur = self.df["Author"].value_counts()
        for author in num_occur.index:
            weight = 100 / num_occur[author]
            self.weights[author] = weight


    def _add_candidates(self):
        '''
        Adds most likely candidates found by Embedder to self.df
        '''

        print("Finding most likely candidates for each game message!")
        self._compute_weights()
        candidate_idx = self.embedder.get_candidate_idxs(hyper_params["processed_path"] + "/embeddings_shortlist.npy")
        candidates = []
        count = 0
        for i, idx_list in enumerate(candidate_idx):

            sim_msgs = self.df.iloc[idx_list]
            sim_authors = sim_msgs["Author"].value_counts()
            og_author = self.df.iloc[i]["Author"]

            # weigh the author similarity scores
            for author in sim_authors.index:
                sim_authors[author] = np.ceil(self.weights[author] * sim_authors[author])
            sim_authors = sim_authors.sort_values(ascending = False)[:4]

            # add original author to the sim_authors, but take note
            if og_author not in sim_authors.index:
                count += 1
                new_index = list(sim_authors.index)
                new_index[-1] = og_author
                sim_authors.index = new_index
            try: 
                candidates_str = ""
                for idx in range(hyper_params["candidates"]):
                    candidates_str += sim_authors.index[idx]
                    if idx != hyper_params["candidates"] - 1:
                        candidates_str += " "
                candidates.append(candidates_str)
            except:
                raise Exception(f"Not enough likely authors found for {hyper_params['candidates']} candidates per message! Try reducing \'candidates\' hyper param or increasing \'k_similar\' hyper param.")

        print(f"Original author different from top 4 {count}/{candidate_idx.shape[0]}. Original authors subsituted in!")
        self.df["Candidates"] = candidates
    
    def create_history(self, save_path: str):
        '''
        Creates sorted history of messages and saves it to the requested file.
        '''
        print("Creating history!")
        start = time.time()
        self._cleanup() 
        self.history["Date"] = pd.to_datetime(self.history["Date"], utc=True)
        self.history = self.history.sort_values("Date")
        self.history.index = np.arange(len(self.history))
        self.history.to_csv(save_path)
        print(f"History created. ({time.time() - start}s)")

    def create_gamefile(self, save_path: str):
        '''
        Saves the chosen unique message
        '''
        print("Creating gamefile!")
        start = time.time()
        self._cleanup2()
        self._get_unique()
        self.df = self.df.iloc[self.indices]
        self.df.index = np.arange(len(self.df))
        self.df.to_csv(save_path)
        self._add_candidates()
        self.df.to_csv(save_path)
        print(f"Gamefile created. ({time.time() - start}s)")

