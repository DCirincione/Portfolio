from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from supabase import create_client
from dotenv import load_dotenv
import os
import json
import random

load_dotenv(".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/projects")
def get_projects():
    response = supabase.table("projects").select("*").order("display_order").execute()
    return response.data

@app.get("/api/work")
def get_work():
    response = supabase.table("work").select("*").order("display_order").execute()
    return response.data

@app.get("/project/{project_id}")
def project_page(request: Request, project_id: int):
    return templates.TemplateResponse(request, "project.html", {"project_id": project_id})
    
@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    return response.data

@app.get("/about")
def about_page(request: Request):
    return templates.TemplateResponse(request, "about.html")


###Interactive Prudh Project
all_games = {}
def load_game_log(filepath, game_num):
    import sys
    sys.path.insert(0, 'prudhaProject')
    import GameRules as Grules

    statelist = []
    movelist = []
    players = {}

    def initial_state(filename):
        logfile = open(filename)
        line_num = 0
        for line in logfile:
            if line_num == 4:
                return json.loads(line)
            line_num += 1
        return {}
    
    game_state = initial_state(filepath)
    logfile = open(filepath)
    line_num = 0

    for line in logfile:
        if line_num == 0:
            words = line.split()
            players['Light'] = words[3]
        if line_num == 1:
            words = line.split()
            players['Dark'] = words[3]
        if line_num == 2:
            words = line.split()
            game_state['Turn'] = words[0]
        if line[0] == "{":
            dict = json.loads(line)
            if 'Row' in dict:
                game_state = Grules.playMove(game_state, dict)
                movelist.append(dict)
            else:
                game_state = dict
            statelist.append(game_state)
        line_num += 1

    all_games[game_num] = {
        'statelist': statelist,
        'movelist': movelist,
        'players': players
    }

def load_all_games():
    game_dir = 'prudhaProject/game_data'
    for i, filename in enumerate(sorted(os.listdir(game_dir))):
        if filename.endswith('.log'):
            load_game_log(os.path.join(game_dir, filename), i)

load_all_games()

@app.get("/demo/{project_id}")
def demo_page(request: Request, project_id: int):
    if project_id == 5:
        game_num = random.randint(0, len(all_games) - 1)
        return templates.TemplateResponse(request, "watchgame.html", {"game_num": game_num})
    if project_id == 6:
        return templates.TemplateResponse(request, "stats_predictor.html")
    
@app.get("/getplayers/")
def getplayers(game: int = 0):
    return all_games[game]['players']

@app.get("/gamestate/{num}")
def gamestate(num: int, game: int = 0):
    statelist = all_games[game]['statelist']
    if num < 0:
        num = 0
    if num >= len(statelist):
        num = len(statelist) - 1
    return statelist[num]

@app.get("/gamemove/{num}")
def gamemove(num: int, game: int = 0):
    movelist = all_games[game]['movelist']
    if num < 0:
        num = 0
    if num >= len(movelist):
        return {"Row": -1, "Col": -1, "Direction": "W"}
    return movelist[num]


###Ai NFL predictor
import sys
sys.path.insert(0, 'AiNFLProject')

@app.get("/demo/6")
def nfl_demo(request: Request):
    return templates.TemplateResponse(request, "stats_predictor.html")

@app.get("/api/nfl/projections")
async def get_nfl_projections(position: str = "WR", season: int = 2025, scoring: str = "ppr", top: int = 10):
    try:
        import sys
        sys.path.insert(0, 'AiNFLProject')
        from fantasy_ml import predict_upcoming_week_topn
        from nfl import get_top_players_week
        try:
            df = predict_upcoming_week_topn(season=season, position=position, scoring=scoring, top_n=top)
            return {"rows": df.to_dict(orient="records"), "mode": "prediction"}
        except (ValueError, ConnectionError, Exception) as e:
            if "No schedule data" in str(e) or "404" in str(e) or "Not Found" in str(e):
                fallback_season = season - 1 if "404" in str(e) or "Not Found" in str(e) else season
                week, df = get_top_players_week(season=fallback_season, week=None, position=position, top_n=top, scoring=scoring)
                return {"rows": df.to_dicts(), "week": week, "mode": "historical"}
            raise e
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}