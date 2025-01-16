from enum import Enum


class ArrangementStatus(Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
