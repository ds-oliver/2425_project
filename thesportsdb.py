# %%
# imports
import requests
import json
import pandas as pd
from datetime import datetime
from datetime import timedelta
import os
import time
import sys
import logging
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from pathlib import Path
import thesportsdb
from unidecode import unidecode

# %%
# logging

logging.basicConfig(
    filename="sportsdb.log", level=logging.INFO, format="%(asctime)s - %(message)s"
)
logging.info("Started")

# %%
DOWNLOAD_DIR = Path("club-badges")
DOWNLOAD_DIR_EPL = DOWNLOAD_DIR / "epl"
os.makedirs(DOWNLOAD_DIR_EPL, exist_ok=True)

DOWNLOAD_PLAYER_DIR = Path("media/epl")
DOWNLOAD_PLAYER_DIR_EPL = DOWNLOAD_PLAYER_DIR / "people"
DOWNLOAD_LEAGUE_DIR_EPL = DOWNLOAD_PLAYER_DIR_EPL / "league"

os.makedirs(DOWNLOAD_PLAYER_DIR_EPL, exist_ok=True)
os.makedirs(DOWNLOAD_LEAGUE_DIR_EPL, exist_ok=True)

# %%
# Replace YOUR_API_KEY with your actual API key
api_key = "60130162"
league_name = "English Premier League"
league_id = "4328"


