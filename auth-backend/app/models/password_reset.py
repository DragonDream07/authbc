from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class PasswordReset:
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None
