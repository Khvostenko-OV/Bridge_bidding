DB_NAME = "bridge_bidding"
DB_DSN = {
    "host": "db.isjtcoazgoecctdzvwrt.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "lw68sxbo9HxgQlmI",
    "sslmode": "require",
}

import streamlit as st

CARDS = {"1": 10, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "J": 11, "Q": 12, "K": 13, "A": 14}
VULN = [0, 1, 2, 3, 1, 2, 3, 0, 2, 3, 0, 1, 3, 0, 1, 2]
