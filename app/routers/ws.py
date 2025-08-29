from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid
from app.services.game_service import get_room

router = APIRouter()

@router.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    await websocket.accept()

    room = get_room(room_id)
    if not room:
        await websocket.send_text("Esa sala no existe 🚫")
        await websocket.close()
        return

    player_id = str(uuid.uuid4())
    room.add_player(player_id, websocket)
    await websocket.send_text(f"Hola {player_name}, estás en la sala {room.name}")

    try:
        while True:
            if len(room.players) == room.max_players and not room.started:
                room.assign_roles()
                for pid, ws in room.players.items():
                    await ws.send_text(f"Tu rol es: {room.roles[pid]}")
            await websocket.receive_text()
    except WebSocketDisconnect:
        del room.players[player_id]
