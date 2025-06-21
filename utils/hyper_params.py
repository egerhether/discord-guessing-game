hyper_params = {
    "server_name": "SERVER NAME",
    "data_path": "data", # directory under which exported message files are located
    "processed_path": "processed", # directory under which preprocessed messages will be saved
    "game_save_path": "saved", # directory under which game save state will be saved
    "users_to_include": ["user1", "user2"],
    "k_similar": 45, # number of most similar messages to find, used for candidate prediction
    "distance_threshold": 0.95, # threshold for out-of-norm message filtering
    "candidates": 4, # number of author candidates to save for each game message
}
