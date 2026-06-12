import sys
sys.path.insert(0, 'AiNFLProject')
from fantasy_ml import predict_upcoming_week_topn
from nfl import get_top_players_week
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv(".env.local")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))

positions = ["WR", "RB", "QB", "TE"]
season = 2025
scoring = "ppr"

for position in positions:
    try:
        df = predict_upcoming_week_topn(season=season, position=position, scoring=scoring, top_n=20)
        rows = df.to_dict(orient="records")
        mode = "prediction"
        week = int(rows[0]["predicted_week"])
    except Exception:
        week, df_pl = get_top_players_week(season=season, week=None, position=position, top_n=20, scoring=scoring)
        rows = df_pl.to_dicts()
        mode = "historical"

    for row in rows:
        supabase.table("nfl_predictions").insert({
            "position": position,
            "season": season,
            "scoring": scoring,
            "week": week,
            "mode": mode,
            "player_name": row.get("player_name") or row.get("player"),
            "team": row.get("team"),
            "predicted_fantasy_points": row.get("predicted_fantasy_points"),
            "fantasy_points": row.get("fantasy_points"),
            "fp_prev1": row.get("fp_prev1"),
            "fp_roll3": row.get("fp_roll3"),
            "fp_roll5": row.get("fp_roll5"),
            "fp_season_avg": row.get("fp_season_avg"),
            "def_team": row.get("def_team"),
        }).execute()
    print(f"Inserted {position}")