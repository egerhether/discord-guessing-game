from utils.processor import Processor
from utils.hyper_params import hyper_params
import os

if __name__ == "__main__":
    if not os.path.exists(hyper_params["processed_path"]):
        os.mkdir(hyper_params["processed_path"])
    if not os.path.exists(hyper_params["game_save_path"]):
        os.mkdir(hyper_params["game_save_path"])
    print(f'''
Performing preprocessing of discord messages with following settings:
---------------------------------------------------------------------
Server name: {hyper_params['server_name']},
Users to include: {hyper_params['users_to_include']}, 
Data path: {hyper_params['data_path']},
Processed path: {hyper_params['processed_path']},
Game save path: {hyper_params['game_save_path']},
Threshold for unique messages: {hyper_params['distance_threshold']},
Number of messages in cadidate search: {hyper_params['k_similar']},
Number of candidates for each message: {hyper_params['candidates']}
---------------------------------------------------------------------
''')
    processor = Processor(hyper_params["data_path"])
    processor.create_history(hyper_params["processed_path"] + "/history.csv")
    processor.create_gamefile(hyper_params["processed_path"] + "/game.csv")
