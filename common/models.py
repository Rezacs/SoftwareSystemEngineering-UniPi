from dataclasses import dataclass


@dataclass
class FootballRecord:
    player_id: int
    short_name: str
    long_name: str
    age: int
    height_cm: float
    weight_kg: float
    club_name: str
    league_name: str
    nationality_name: str
    preferred_foot: str
    overall: float
    potential: float
    shooting: float
    passing: float
    dribbling: float
    defending: float
    physic: float


@dataclass
class MedicalRecord:
    player_id: int
    player_name: str
    position: str
    main_position: str
    current_club_name: str
    days_missed: float
    games_missed: float
    injury_reason: str
    season_name: str


@dataclass
class SocialRecord:
    player_id: int
    short_name: str
    number_of_likes: int
    number_of_followers: int

@dataclass
class CombinedPlayerRecord:
    player_id: int
    football: FootballRecord | None
    medical: MedicalRecord | None
    social: SocialRecord | None
    label: str | None = None
