from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from supabase import create_client
from dotenv import load_dotenv
import os

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