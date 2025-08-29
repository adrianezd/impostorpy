from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.services.game_service import create_room

router = APIRouter()

@router.get("/")
async def get_form():
    return HTMLResponse("""
    <h2>Juego del Blanco</h2>
    <form action="/create_room" method="get">
        <label>Nombre: <input type="text" name="player_name" required></label><br>
        <label>Nombre sala: <input type="text" name="room_name" required></label><br>
        <label>Número de jugadores: <input type="number" name="max_players" value="5" min="2"></label><br>
        <button type="submit">Crear sala</button>
    </form>
    """)

@router.get("/create_room")
async def create(player_name: str, room_name: str, max_players: int):
    room = create_room(room_name, max_players)
    return {
        "message": f"Sala '{room.name}' creada con ID {room.id}",
        "join_url": f"/ws/{room.id}/{player_name}"
    }
