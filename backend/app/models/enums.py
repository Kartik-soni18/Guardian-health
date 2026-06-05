"""GuardianHealth enumeration types for triage, chat, user, and routing domains."""

from enum import Enum


class TriageLevel(str, Enum):
    """5-level emergency triage scale (ESI-inspired)."""

    LEVEL_1 = "level_1"  # Resuscitation — imminent life threat
    LEVEL_2 = "level_2"  # Emergent — high risk, rapid deterioration
    LEVEL_3 = "level_3"  # Urgent — multiple resources needed
    LEVEL_4 = "level_4"  # Less Urgent — single resource
    LEVEL_5 = "level_5"  # Non-Urgent — exam/advice only
    UNKNOWN = "unknown"


TRIAGE_LEVEL_TITLES: dict[str, str] = {
    TriageLevel.LEVEL_1: "Resuscitation",
    TriageLevel.LEVEL_2: "Emergent",
    TriageLevel.LEVEL_3: "Urgent",
    TriageLevel.LEVEL_4: "Less Urgent",
    TriageLevel.LEVEL_5: "Non-Urgent",
    TriageLevel.UNKNOWN: "Unclassified",
}


class ChatStatus(str, Enum):
    """Lifecycle states for a patient chat session."""

    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"
    FLAGGED = "flagged"


class UserRole(str, Enum):
    """RBAC roles within the GuardianHealth platform."""

    PATIENT = "patient"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    RESEARCHER = "researcher"


class RoutingDecision(str, Enum):
    """Recommended care routing outcome from the triage engine."""

    CALL_911 = "call_911"
    ED_NOW = "ed_now"
    ED_SAME_DAY = "ed_same_day"
    URGENT_CARE = "urgent_care"
    PRIMARY_CARE = "primary_care"
    SELF_CARE = "self_care"
    TELEMEDICINE = "telemedicine"
    PHARMACY = "pharmacy"
    FOLLOW_UP = "follow_up"
    NONE = "none"
