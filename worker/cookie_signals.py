# cookie_signals.py
import json
from dataclasses import dataclass, asdict
from typing import Optional, Any, Dict
from enum import Enum
 
class SignalType(Enum):
    COOKIE_NEEDED = "cookie_needed"
    COOKIE_UPDATED = "cookie_updated"
    BATCH_UPDATE = "batch_update"
    COOKIE_RESPONSE = "cookie_response"
 
@dataclass
class SignalMessage:
    signal_type: SignalType
    request_id: str
    url: Optional[str] = None
    immediate: bool = False
    priority: str = "normal"
    data: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
    
    def to_json(self) -> str:
        return json.dumps({
            **asdict(self),
            'signal_type': self.signal_type.value
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SignalMessage':
        data = json.loads(json_str)
        data['signal_type'] = SignalType(data['signal_type'])
        return cls(**data)