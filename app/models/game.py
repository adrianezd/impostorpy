import uuid, random
from typing import Dict
from fastapi import WebSocket

class Room:
    def __init__(self, name: str, max_players: int):
        self.id = str(uuid.uuid4())[:6]
        self.name = name
        self.max_players = max_players
        self.players: Dict[str, WebSocket] = {}
        self.roles: Dict[str, str] = {}
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
