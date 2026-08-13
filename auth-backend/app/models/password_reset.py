from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class PasswordReset:
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: Optional[datetime] = None
