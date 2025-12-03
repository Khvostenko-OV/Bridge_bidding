import streamlit as st

DB_DSN = st.secrets["db"]

CARDS = {"1": 10, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "J": 11, "Q": 12, "K": 13, "A": 14}
VULN = [0, 1, 2, 3, 1, 2, 3, 0, 2, 3, 0, 1, 3, 0, 1, 2]

README = """
    In **Read only** mode you can as *Anonym* browse all systems.
    Or just **Register** with *login* and *password* (*username* is also recommended).
    As **User** you can new systems create or any existent system clone and then edit.
    
    Enter **Short name** of your system (it should be unique). 
    Enter **Title** (long name) and description
    of the main principles (use markdown).
    
    Create the tree of bids with descriptions. 
    You can also define parameters of each bid
    (point count limits, balanced or not, number of cards in the suits).
    Who knows why?
    
    There are some auto-replaces:
    - _c ⟶ ♣️
    - _d ⟶ ♦️ 
    - _h ⟶ ♥️
    - _s ⟶ ♠️
    - _+ ⟶ ♥️♠️
    - _- ⟶ ♣️♦️ 
    
    Toggle **With opps** switch between one-side and concurrent bidding.
    
    Enjoy!
"""
