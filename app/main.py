import os, uuid, random
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app = FastAPI()

rooms = {}  # id -> info de sala


class Room:
    def __init__(self, name: str, max_players: int):
        self.id = str(uuid.uuid4())[:6]  # 6 chars aleatorios
        self.name = name
        self.max_players = max_players
        self.players = []   # lista de nombres
        self.roles = {}
        self.started = False

    def assign_roles(self):
        num_blancos = 1 + (self.max_players - 5) // 4 if self.max_players > 5 else 1
        blancos = random.sample(self.players, num_blancos)
        for p in self.players:
            self.roles[p] = "BLANCO" if p in blancos else "NORMAL"
        self.started = True


@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create_room", response_class=HTMLResponse)
async def create_room(request: Request, player_name: str, room_name: str, max_players: int):
    room = Room(name=room_name, max_players=max_players)
    rooms[room.id] = room
    room.players.append(player_name)
    return templates.TemplateResponse("room.html", {"request": request, "room": room})



@app.get("/join/{room_id}", response_class=HTMLResponse)
async def join_room(request: Request, room_id: str):
    room = rooms.get(room_id)
    if not room:
        return HTMLResponse("Sala no encontrada ❌", status_code=404)
    return templates.TemplateResponse("join.html", {"request": request, "room": room})


@app.post("/join/{room_id}", response_class=HTMLResponse)
async def join_room_post(request: Request, room_id: str, player_name: str = Form(...)):
    room = rooms.get(room_id)
    if not room:
        return HTMLResponse("Sala no encontrada ❌", status_code=404)
    room.players.append(player_name)
    return RedirectResponse(f"/room/{room_id}", status_code=303)


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def show_room(request: Request, room_id: str):
    room = rooms.get(room_id)
    if not room:
        return HTMLResponse("Sala no encontrada ❌", status_code=404)

    return templates.TemplateResponse("room.html", {
        "request": request,
        "room": room,
        "join_url": f"http://127.0.0.1:8000/join/{room.id}"
    })


@app.post("/start/{room_id}", response_class=HTMLResponse)
async def start_game(request: Request, room_id: str):
    room = rooms.get(room_id)
    if not room:
        return HTMLResponse("Sala no encontrada ❌", status_code=404)
    room.assign_roles()
    return templates.TemplateResponse("results.html", {"request": request, "room": room})
