from enum import Enum


class JobType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERN = "Internship"
    FREELANCE = "Freelance"
    TEMPORARY = "Temporary"
    UNKNOWN = "Unknown"


class ExperienceLevel(str, Enum):
    ENTRY = "Entry"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    EXECUTIVE = "Executive"
    UNKNOWN = "Unknown"