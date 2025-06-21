from collections import defaultdict
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import altair as alt
import json

from streamlit_autorefresh import st_autorefresh
from utils.hyper_params import hyper_params

class Game:
    def __init__(self):
        # initialize for first/subsequent load
        if "page" not in st.session_state:
            st.set_page_config("Who said that?")
            st.session_state.page = 0  
            self.indices = []
        else:
            self.indices = np.load(hyper_params["game_save_path"] + "/indices.npy") 
            self.num_msg = len(self.indices)

        st.session_state.role = st.query_params.get("role", "player") 


        if "game_state" not in st.session_state:
            st.session_state.game_state = {
                "page_id": 0,
                "answers": defaultdict(list, []),
            }
        else:
            with open(hyper_params["game_save_path"] + "/state.json", "r") as f:
                st.session_state.game_state = json.load(f)
                # if not waiting for everyone to answer
                if not (st.session_state.page == -1 and st.session_state.game_state["page_id"] % 2 == 1):
                    st.session_state.page = st.session_state.game_state["page_id"]

        # data and display
        self.placeholder = st.empty()
        self.data = pd.read_csv(hyper_params["processed_path"] + "/game.csv")
        self.history = pd.read_csv(hyper_params["processed_path"] + "/history.csv")

        # decision tree what page to load
        if st.session_state.page == 0:
            self._main_menu()
        elif st.session_state.page == -1:
            self._blank_page()
        elif st.session_state.page / 2 > self.num_msg:
            self._final_page()
        elif st.session_state.page % 2 == 1:
            self._game_page(st.session_state.page)
        else:
            self._context_page(st.session_state.page)
    
    def _nextpage(self):
        '''
        Callback for getting to the next page. Called only on host. 
        Reads the current state from file (player answers) and updates it.
        '''
        st.session_state.game_state["page_id"] += 1
        # called from host always, so always first read player updates
        with open(hyper_params["game_save_path"] + "/state.json", "r") as f:
            new_state = json.load(f)
        if new_state["answers"] != {}:
            st.session_state.game_state["answers"] = new_state["answers"]
        # then save 
        with open(hyper_params["game_save_path"] + "/state.json", "w") as f:
            json.dump(st.session_state.game_state, f)
        st.session_state.page = st.session_state.game_state["page_id"]

    def _guess(self, point, player):
        '''
        Callback for performing a guess. Called only by player.
        Updates state with new answer.
        '''
        # initialization
        if player not in st.session_state.game_state["answers"]:
            st.session_state.game_state["answers"][player] = []
        # vote history
        st.session_state.game_state["answers"][player].append(point)
        # load current state and override only current player
        new_state_player = st.session_state.game_state["answers"][player]
        with open(hyper_params["game_save_path"] + "/state.json", "r") as f:
            st.session_state.game_state = json.load(f)
        st.session_state.game_state["answers"][player] = new_state_player
        with open(hyper_params["game_save_path"] + "/state.json", "w") as f:
            json.dump(st.session_state.game_state, f)

        st.session_state.page = -1

    def _reset(self):
        '''
        Callback for resetting the game state. Called only by host.
        '''
        state = {
            "page_id": 0,
            "answers": {}
        }
        with open(hyper_params["game_save_path"] + "/state.json", "w") as f:
            st.session_state.game_state = json.dump(state, f)

    def _blank_page(self):
        st.title("Waiting for host!")
        st_autorefresh(2000)

    def _main_menu(self):
        '''
        Main menu page.
        '''
        if st.session_state.role == "host":
            with self.placeholder.container():
                st.markdown("# \'Who said that?\' Fruit Bowl Edition!")
                num_msg = st.text_input("Type num of messages to guess!", )
                if num_msg == '': # before anything is typed
                    pass 
                else: # get num messages to sample, sample them, save
                    self.num_msg = int(num_msg)
                    indices = np.random.choice(np.arange(len(self.data)), size = self.num_msg)
                    np.save(hyper_params["game_save_path"] + "/indices.npy", indices)
                st.button("Play", on_click=self._nextpage)
                st.button("Reset", on_click=self._reset)
                #st.write(f"Number of connected players {st.session_state}")
        if st.session_state.role == "player":
            with self.placeholder.container():
                st.title("Welcome!")
                player_name = st.text_input("Type in your name!") 
                st.session_state.player_name = player_name
                if st.session_state.player_name:
                    st_autorefresh(2000)


    def _game_page(self, page: int):
        '''
        Question page.
        '''
        index = self.indices[page // 2] # get index of msg to display
        message = self.data.iloc[index]["Content"] # get content of msg
        options = self.data.iloc[index]["Candidates"].split(" ") # answer options
        if st.session_state.role == "host":
            with self.placeholder.container():
                text = f"""
                # Who said...
                ## :blue[\"{message}\"]
                """
                st.markdown(text)
                for option in options:
                    st.markdown("### " + option) 
                st.button("Next", on_click=self._nextpage)
                st.button("Reset", on_click=self._reset)
        if st.session_state.role == "player":
            corr_author = self.data.iloc[index]["Author"]
            with self.placeholder.container():
                for option in options:
                    point = 1 if option == corr_author else 0
                    st.button(option, on_click=self._guess, args = [point, st.session_state.player_name])


    def _context_page(self, page: int):
        '''
        Page showing context of messages.
        '''
        if st.session_state.role == "host":
            data_index = self.indices[(page - 1) // 2] # get index of the message displayed
            corr_msg = self.data.iloc[data_index]["Content"] # get text of the message displayed
            index = self.history.index[self.history["Content"] == corr_msg][0]
            messages = self.history.iloc[(index - 3):(index + 4)]["Content"]
            authors = self.history.iloc[(index - 3):(index + 4)]["Author"]
            dates = self.history.iloc[(index - 3):(index + 4)]["Date"]
            with self.placeholder.container():
                for date, (author, msg) in zip(dates, zip(authors, messages)): # display context
                    date = dt.datetime.fromisoformat(date)
                    date = date.strftime("%d-%m-%Y %H:%M:%S")
                    if corr_msg == msg:
                        text = f"""
                        :rainbow: :rainbow[**{author}**] :rainbow:
                        :small[:gray[{date}]]
                        > {msg}
                        """
                    else:
                        text = f"""
                        **{author}**
                        :small[:gray[{date}]]
                        > {msg}
                        """
                    st.markdown(text)
                st.button("Next", on_click=self._nextpage)
                st.button("Reset", on_click=self._reset)
        if st.session_state.role == "player":
            st.title("Waiting for host!")
            st_autorefresh(2000)

    
    def _final_page(self):
        '''
        Page with a thank you message and results.
        '''
        with self.placeholder.container():
            st.markdown("# :rainbow[THANKS FOR PLAYING <3]")
            if st.session_state.role == "host":
                results = {"name": [],
                           "result": []}
                for player in st.session_state.game_state["answers"].keys():
                    results["name"].append(player)
                    results["result"].append(np.sum(st.session_state.game_state["answers"][player]))
                
                results = pd.DataFrame(results)
                results = results.sort_values("result", ascending = False).reset_index(drop=True)

                colors = ["#FF66B2", "#914AE2", "#599ED2", "#69BF56", "#CEC01C", "#D77A37", "#CF2F1D"]
                results["color"] = colors[:len(results)]

                bars = alt.Chart(results).mark_bar().encode(
                    x=alt.X('name:N', title='Player', axis=alt.Axis(labelAngle=0, labelFontSize=20, titleFontSize=0)),
                    y=alt.Y('result:Q', title='', axis=alt.Axis(labels=False, ticks=False, grid=False)),
                    color=alt.Color('name:N', scale=alt.Scale(range=colors[:len(results)]), legend=None)
                )

                # labels of score above a chart
                labels = alt.Chart(results).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,  
                    fontSize=20
                ).encode(
                    x='name:N',
                    y='result:Q',
                    text='result:Q'
                )
                
                # add together for complete char
                chart = (bars + labels).properties(
                    width=600,
                    height=400
                )
                st.altair_chart(chart, use_container_width=True)
                st.button("Reset", on_click=self._reset)

