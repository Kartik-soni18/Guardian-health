"""GuardianHealth enumeration types for triage, chat, user, and routing domains."""

from enum import Enum


class TriageLevel(str, Enum):
    """Emergency Severity Index (ESI) inspired triage levels.

    Levels range from EMERGENCY (immediate life threat) to
    SELF_CARE (mild, self-limiting symptoms).
    """

    EMERGENCY = "emergency"          # ESI 1: Life-threatening, immediate intervention
    URGENT = "urgent"                # ESI 2: High risk, dangerous presentation
    PROMPT = "prompt"                # ESI 3: Multiple resources, stable vitals
    LESS_URGENT = "less_urgent"      # ESI 4: Single resource likely
    NON_URGENT = "non_urgent"        # ESI 5: No resources, self-care
    SELF_CARE = "self_care"          # Minor, OTC/self-management sufficient
    UNKNOWN = "unknown"              # Insufficient information to classify


class ChatStatus(str, Enum):
    """Lifecycle states for a patient chat session."""

    ACTIVE = "active"                # Ongoing conversation
    PAUSED = "paused"                # Temporarily suspended (e.g., awaiting follow-up)
    CLOSED = "closed"                # Completed normally
    ARCHIVED = "archived"            # Long-term storage, read-only
    FLAGGED = "flagged"              # Manually flagged for clinical review


class UserRole(str, Enum):
    """RBAC roles within the GuardianHealth platform."""

    PATIENT = "patient"              # Standard end-user seeking triage
    CLINICIAN = "clinician"          # Licensed provider with elevated access
    ADMIN = "admin"                  # Platform administrator
    RESEARCHER = "researcher"        # Data/research access (de-identified)


class RoutingDecision(str, Enum):
    """Recommended care routing outcome from the triage engine."""

    CALL_911 = "call_911"            # Immediate EMS activation
    ED_NOW = "ed_now"                # Emergency department — go now
    ED_SAME_DAY = "ed_same_day"      # Emergency department — same day
    URGENT_CARE = "urgent_care"      # Urgent care or walk-in clinic
    PRIMARY_CARE = "primary_care"    # Primary care / GP visit
    SELF_CARE = "self_care"          # Home management with OTC
    TELEMEDICINE = "telemedicine"    # Virtual visit appropriate
    PHARMACY = "pharmacy"            # Pharmacist consultation
    FOLLOW_UP = "follow_up"          # Schedule routine follow-up
    NONE = "none"                    # No routing indicated