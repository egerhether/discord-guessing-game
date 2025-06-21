# Discord guessing game! 
This repository contains a web app based game, which you can host on your local network to guess which of your friends wrote a discord message. People joining can vote and tally a score!

This program processes chat logs to find the most unique messages making for an interesting guessing game where boring messages are unlikely to show up! It also automates guessing options shown such that the most likely senders are chosen, which makes guessing more difficult. This game is suitable for multilingual discord servers.

## Installation

Clone this repository into your desired location with
```
git clone https://github.com/egerhether/discord-guessing-game.git
```

Main prerequisite for installing the dependencies of this project is [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html). 

After installing conda, navigate inside `discord-guessing-game` and run 
```
conda env create -f environment.yaml
conda activate discord
```
This will install all python libraries necessary to run the game and put you in a conda environment with access to those libraries.

## Usage

After installing the necessary python libraries, create a `data` directory within `discord-guessing-game`. To provide data for the game, download your desired discord server chats using [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) and copy them into `discord-guessing-game/data`. IMPORTANT: supported file format for preprocessing is .csv so make sure exported files are of this format!

Before you can start preparing gamefiles from your chats look into `utils/hyper_params.py` file, which contains global settings for preprocessing chats and playing the game. Below is a table explaining each setting, optional settings are marked with * and do not need to be changed for the game to work properly.

| Name | Description |
|------|-------------|
| `server_name` | Name of your server. Set it to the name of the server that will be displayed in the main menu of the game |
| `data_path`* | Directory where raw exported chat files are placed. Optional. |
| `processed_path`* | Directory where processed chat files will be placed. Optional. |
| `game_save_path`* | Directory where game state will be saved for interaction between host and players. Optional. |
| `users_to_include` | List of users from whom you want messages to be included in the game. Meant for filtering out bot or banned user messages. |
| `k_similar` | Number of similar messages left after searching. Increase if error message prompts you to. For more information see [k_similar](#k_similar) below. |
| `distance_threshold`* | Distance from the mean for a message to be considered unique. Optional. For more information see [Threshold](#threshold) below. |
| `candidates`* | Number of candidates found and presented for each message. Optional. Default is 4. |

Change your desired settings and save the file. You can always change something more later and rerun processing :).

You are now ready to processes your raw exported chats. Make sure you're in a conda environment by running 
`conda activate discord`
and in the `discord-guessing-game` directory run
```
python preprocess_main.py
```
This will create all necessary files for the game to run. If you encounter errors, read them carefully and act accordingly. See [Errors](#Possible-errors) for more detailed instructions.

To run the game run 
```
streamlit run main.py --server.address=<your-local-ip> --server.port=8501
```

This will open your browser with the game in the player mode. To switch to host mode edit the url by adding `/?role=host` at the end and press enter. Players can now join the game from their devices if they're connected to the same network as the host machine. They can do so by navigating to the url shown in the terminal after running the command above. It is going to be 
`http://<your-local-ip>:8501`. Going to this url defaults to player mode.

## Playing the game

The game requires a host, which is in charge of presenting information and determining the current sub-page presented to players. Host instance is also responsible for showing the final score.

When connecting to the website host will be shown a main menu with title of the game and an text input field for how many questions the game will consist of. The players will be presented with a text input of their in-game name and after they submit one, they will enter a waiting state for the host to submit number of questions and start the game.

Then a gameplay loop begins, where the host will show a question (of the form "Who said... \<text of the message\>") and possible answers (number of them determined by `candidates` setting in `hyper_params.py`). Players with see buttons with the answers on them, pressing any of them counts as a guess towards that answer and saves it in the game state. Players then enter a waiting state for the host to play next. IMPORTANT: host should make sure all players submitted their answers before clicking `Next`!

After the question, host will show the context of the message - 3 messages before and 3 messages after the message being guessed - with a highlighted author. Players will be in the waiting state for the entirety of this processes, which continues after the host clicks `Next`. 

The gameplay loop continues alternating between message and context, until the number of messages set by the host at the beginnign is reached. Players are shown a "Thanks for playing" message, while the host view will show results.

Sometimes a player might not get presented with new options - this is a bug and so far I do not know why this happens. In this situation everyone should stop playing, and affected player should refresh the page. They will be prompted to enter their name and after doing so they should be able to contiue playing as normal. Sometimes only results from the reconnections will be counted and the answers from before will be attributed to an empty player at the results screen. 

## Possible errors

This section is devoted to errors that may show up during preprocessing and describe what to do if they occur.

1. **Create data directory and put exported files there!**

This error occurs if the program detected no .csv files in the data directory. See [Usage](#Usage) section for more information.

2. **Not enough likely authors found for N candidates per message! ...**

This error occurs if the program finds too little likely authors than requested in `hyper_params['candidates']`. You can either reduce `hyper_params['candidates']` or increase `hyper_params['k_similar']` until the error disappears. Note: increasing `hyper_params['k_similar']` will increase running time of the preprocessing function, but the increase should not be excessive. For more information about why this happens see [k_similar](#k_similar).

3. **Do not call this function before ...**

This error should not occur when the original code is ran. If you're getting this error, make sure your alterations to the code follow the required order of file creations within `Embedder` and `Processor` objects!

## Method

This section is aimed at users interested in HOW the program (specifically the preprocessing script) achieves its goals. 

In short, during preprocessing after history of all messages is created to provide context for message in the game, messages to be taken into account during the game are obtained by filtering the message history further. A regular cleanup is performed with links, mentions, and stock messages like "Joined the server." are removed. Additionally, only messages between 3 and 10 words are taken into account.

After that all messages chosen in this process are encoded using [LaBSE](https://github.com/bojone/labse) model. LaBSE is a language-agnostic sentence encoder based on BERT, which provides vector representations for sentences given to it as input. In this manner, we obtain a vector encoding meaning of each message. To find unique messages making for an interesting guessing game, we compute a mean of all encodings (a sort of mean message sent in the server) and then compute L2 distance between the mean and each encoding. In this way we quantify how far away from average a message is. This system is not perfect, but in practice provides a good heuristic way to find interesting messages.

### threshold

One of the hyper parameters set at the beginning is `hyper_params['distance_treshold']`. This is by default set to 0.95, and determines the minimum L2 distance a message should be from the mean to be classified as unique and retained in the game set. The higher you set the threshold the more unique messages will remain, but also more messages will be filtered out. To obtained an optimal result it is advised to run the preprocessing multiple times to see how many and of what quality the retained messages are. In my example from around 40000 initially cleaned messages from history around 4000 were left with `hyper_params['distance_threshold']` set to 0.95.

After filtering for unique messages, we need to compute likely candidates for each remaining message. This is done to provide more interesting guessing experience - only people likely to have sent a message are presented as options - at least that's the idea behind it. How the program achieves this is by creating k-nearest neighbours set for each message, that is a set of k most similar messages in meaning (quantified by their embedding). Then their authors are collected and top n (set by `hyper_params['candidates']`) are taken as options to be presented during the game. As this system is highly approximate sometimes the actual author of the message will not be present within that top n. In this case the program removes the least likely of from the top n and substitutes the actual author in.

### k_similar

The other hyper parameter left for further discussion concerns this part of the program. `hyper_params['k_similar']` determines how many similar messages are collected for each message to determine likely candidates. Sometimes an error will be thrown if not enough candidates were collected from the top k and to proceed forward increasing `hyper_params['k_similar]` is advised. Advice for tuning for interested users is to try different `hyper_params['k_similar']` such that the situation where actual author is not part of top n candidates is the smallest. Usually the smaller `hyper_params['k_similar']` the better.


In the end the filtered down and extended with likely candidates gamefile will be saved to the requested location and used as input to the game!


