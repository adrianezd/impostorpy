from app.models.game import Room

# Diccionario global de salas
rooms = {}

def create_room(room_name: str, max_players: int) -> Room:
    room = Room(name=room_name, max_players=max_players)
    rooms[room.id] = room
    return room

def get_room(room_id: str) -> Room:
    return rooms.get(room_id)
