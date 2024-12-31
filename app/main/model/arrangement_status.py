from enum import Enum


class ArrangementStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
