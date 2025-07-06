from dataclasses import dataclass
from datetime import datetime

from surrealdb import RecordID


@dataclass
class tmpVcSpawners:
    id: RecordID
    channel_id: int
    created_at: datetime


@dataclass
class tmpVcs:
    id: RecordID
    channel_id: int
    created_at: datetime
    creator: int
    owner: int
    spawner: RecordID  # tmpVcSpawners.id
