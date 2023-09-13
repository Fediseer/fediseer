import enum

class ReportType(enum.Enum):
    GUARANTEE = 0
    ENDORSEMENT = 1
    CENSURE = 2
    HESITATION = 3

class ReportActivity(enum.Enum):
    ADDED = 0
    DELETED = 1
    MODIFIED = 2

class PMProxy(enum.Enum):
    NONE = 0
    MASTODON = 1
