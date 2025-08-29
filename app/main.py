from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uuid, random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

rooms = {}  # almacena todas las salas activas


# ---------------------
# CLASE ROOM
# ---------------------
class Room:
    def __init__(self, name: str, max_players: int):
        self.id = str(uuid.uuid4())[:6]  # código único corto
        self.name = name
        self.max_players = max_players
        self.players = {}  # player_id -> websocket
        self.roles = {}
        self.started = False

    def add_player(self, player_id: str, websocket: WebSocket):
        self.players[player_id] = websocket

    def assign_roles(self):
        all_ids = list(self.players.keys())
        num_blancos = 1 + (self.max_players - 5) // 4 if self.max_players > 5 else 1
        blancos = random.sample(all_ids, num_blancos)

        for pid in all_ids:
            self.roles[pid] = "BLANCO" if pid in blancos else "NORMAL"

        self.started = True


# ---------------------
# RUTAS NORMALES
# ---------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create_room", response_class=HTMLResponse)
async def create_room(request: Request, player_name: str, room_name: str, max_players: int):
    room = Room(name=room_name, max_players=max_players)

    # comprobar que no se repita el ID
    while room.id in rooms:
        room = Room(name=room_name, max_players=max_players)

    rooms[room.id] = room

    join_url = f"http://127.0.0.1:8000/room/{room.id}"
    return templates.TemplateResponse("room.html", {
        "request": request,
        "room": room,
        "join_url": join_url,
        "players": 1
    })


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def join_room(request: Request, room_id: str):
    room = rooms.get(room_id)
    if not room:
        return HTMLResponse("<h1>❌ Sala no encontrada</h1>", status_code=404)

    return templates.TemplateResponse("room.html", {
        "request": request,
        "room": room,
        "join_url": f"http://127.0.0.1:8000/room/{room.id}",
        "players": len(room.players)
    })

@app.get("/room/{room_id}", response_class=HTMLResponse)
async def join_room(request: Request, room_id: str, player_name: str = None):
    room = rooms.get(room_id)
    if not room:
        return HTMLResponse("<h1>❌ Sala no encontrada</h1>", status_code=404)

    # Si no hay nombre → mostrar formulario de entrada
    if not player_name:
        return templates.TemplateResponse("join.html", {
            "request": request,
            "room": room
        })

    # Si ya hay nombre → mostrar pantalla de espera
    return templates.TemplateResponse("room.html", {
        "request": request,
        "room": room,
        "player_name": player_name
    })

# ---------------------
# WEBSOCKETS
# ---------------------
@app.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    await websocket.accept()
    room = rooms.get(room_id)
    if not room:
        await websocket.send_text("❌ Sala no encontrada")
        await websocket.close()
        return

    player_id = str(uuid.uuid4())
    room.add_player(player_id, websocket)

    # Guardar nombres y ready
    if not hasattr(room, "names"):
        room.names = {}
    room.names[player_id] = player_name
    if not hasattr(room, "ready"):
        room.ready = set()

    await broadcast_players(room)

    try:
        while True:
            msg = await websocket.receive_text()
            import json
            data = json.loads(msg)

            if data["type"] == "ready":
                room.ready.add(player_id)

            if data["type"] == "start":
                # calcular % de jugadores conectados / max_players
                if len(room.players) / room.max_players >= 0.6 and not room.started:
                    room.assign_roles()
                    for pid, ws in room.players.items():
                        await ws.send_json({"type": "role", "role": room.roles[pid]})
                    room.started = True  # marcar que la partida ya empezó


            await broadcast_players(room)

    except WebSocketDisconnect:
        del room.players[player_id]
        del room.names[player_id]
        if player_id in room.ready:
            room.ready.remove(player_id)
        await broadcast_players(room)


async def broadcast_players(room):
    players = list(room.names.values())
    for ws in room.players.values():
        await ws.send_json({"type": "update_players", "players": players})
