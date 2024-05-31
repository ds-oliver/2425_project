from mplsoccer import (
    Pitch,
    VerticalPitch,
    create_transparent_cmap,
    FontManager,
    arrowhead_marker,
)
from matplotlib.font_manager import FontProperties
import warnings

# Database connection parameters
DB_PARAMS = {
    "database": "project_db",
    "user": "hogan",
    "password": "Gunkis#1",
    "host": "localhost",
    "port": "5432",
}

# Warnings
warnings.filterwarnings("ignore")

# Set font
fm_rubik = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/ofl/"
    "rubikmonoone/RubikMonoOne-Regular.ttf"
)

fm_rubik = fm_rubik.prop

fm_ubuntu = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/ufl/" "ubuntu/Ubuntu-Bold.ttf"
)

fm_ubuntu = fm_ubuntu.prop

fm_lato = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/ofl/" "lato/Lato-Bold.ttf"
)

fm_lato = fm_lato.prop

fm_roboto = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/apache/"
    "robotomono/RobotoMono[wght].ttf"
)

fm_roboto = fm_roboto.prop
# ofl/inter
fm_inter = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/ofl/"
    "inter/Inter[slnt,wght].ttf"
)

fm_inter = fm_inter.prop

local_fontpath = "/Users/hogan/Library/CloudStorage/Dropbox/Mac/Documents/GitHub/st_fantrax_dashboard/fonts/DylanCondensed-Medium.ttf"

DylanCondensed = FontProperties(fname=local_fontpath)

local_fontpath_2 = "/Users/hogan/Library/CloudStorage/Dropbox/Mac/Documents/GitHub/st_fantrax_dashboard/fonts/FenomenSans-Regular.ttf"

FenomenSans = FontProperties(fname=local_fontpath_2)

# API Configuration
API_KEY = "60130162"
EPL_ID = "4328"
EFL_CHAMPIONSHIP_ID = "4329"
EFL_LEAGUE_ONE_ID = "4396"
SEASON = "2023-2024"
