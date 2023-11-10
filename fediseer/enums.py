import enum

class ReportType(enum.Enum):
    GUARANTEE = 0
    ENDORSEMENT = 1
    CENSURE = 2
    HESITATION = 3
    CLAIM = 4
    SOLICITATION = 5
    FLAG = 6
    REBUTTAL = 7

class ReportActivity(enum.Enum):
    ADDED = 0
    DELETED = 1
    MODIFIED = 2

class PMProxy(enum.Enum):
    NONE = 0
    MASTODON = 1

class ListVisibility(enum.Enum):
    OPEN = 0
    ENDORSED = 1
    PRIVATE = 2

class InstanceState(enum.Enum):
    UP = 0
    UNREACHABLE = 1
    OFFLINE = 2
    DECOMMISSIONED = 3

class InstanceFlags(enum.Enum):
    RESTRICTED = 0
    MUTED = 1

class BadgeStyle(enum.Enum):
    FULL = 0
    ICON = 1
