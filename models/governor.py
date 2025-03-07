# models/governor.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Governor:
    name: str
    id: str
    power: int = 0
    kill_points: int = 0
    deads: int = 0
    tier1_kills: int = 0
    tier2_kills: int = 0
    tier3_kills: int = 0
    tier4_kills: int = 0
    tier5_kills: int = 0
    rss_assistance: int = 0
    alliance_helps: int = 0
    alliance: str = ""
    kvk_kills: int = 0
    kvk_deads: int = 0
    kvk_severely_wounded: int = 0
    
    @classmethod
    def from_basic_scan(cls, name: str, id_str: str, power: str, kill_points: str):
        """Create Governor from basic scan data."""
        return cls(
            name=name,
            id=id_str,
            power=cls._parse_int(power),
            kill_points=cls._parse_int(kill_points)
        )
    
    @classmethod
    def from_pkd_scan(cls, name: str, id_str: str, power: str, kill_points: str, dead: str):
        """Create Governor from Power + Kill Points + Dead scan data."""
        return cls(
            name=name,
            id=id_str,
            power=cls._parse_int(power),
            kill_points=cls._parse_int(kill_points),
            deads=cls._parse_int(dead)
        )
    
    @classmethod
    def _parse_int(cls, value):
        """Parse integer with error handling."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0