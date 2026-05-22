import os
import swisseph as swe
from datetime import datetime, date, time
import pytz

class AstrologyEngine:
    def __init__(self):
        # Configure the engine to point directly to our local ephemeris data directory
        ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
        swe.set_ephe_path(ephe_path)

    def _convert_to_utc_julian_day(self, birth_date: date, birth_time: time, timezone_str: str) -> float:
        """Converts local birth telemetry into a localized UTC datetime and generates a Julian Day Float."""
        local_tz = pytz.timezone(timezone_str)
        naive_datetime = datetime.combine(birth_date, birth_time)
        
        # Localize naive time and convert cleanly to UTC
        localized_datetime = local_tz.localize(naive_datetime)
        utc_datetime = localized_datetime.astimezone(pytz.utc)
        
        # Calculate fractional UTC hours
        decimal_utc_hour = utc_datetime.hour + (utc_datetime.minute / 60.0) + (utc_datetime.second / 3600.0)
        
        # Generate the precise Julian Day float required by the Swiss Ephemeris core
        julian_day = swe.julday(
            utc_datetime.year, 
            utc_datetime.month, 
            utc_datetime.day, 
            decimal_utc_hour
        )
        return julian_day

    def calculate_natal_planets(self, birth_date: date, birth_time: time, timezone_str: str):
        """Calculates the longitude positions of core planetary bodies."""
        julian_day = self._convert_to_utc_julian_day(birth_date, birth_time, timezone_str)
        
        # Map out the planets we want to calculate using Swiss Ephemeris internal IDs
        target_bodies = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN
        }
        
        planetary_positions = {}
        
        for name, body_id in target_bodies.items():
            # swe.calc_ut returns an array: [longitude, latitude, distance, speed_long, ...]
            # Flag 0 specifies standard ecliptic positions
            result, _ = swe.calc_ut(julian_day, body_id, 0)
            longitude = result[0]
            
            planetary_positions[name] = {
                "absolute_degree": round(longitude, 4),
                "zodiac_sign": self._get_zodiac_sign(longitude)
            }
            
        return planetary_positions

    def _get_zodiac_sign(self, longitude: float) -> str:
        """Maps absolute 360-degree coordinates into the 12 classic signs."""
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        index = int(longitude // 30)
        return signs[index]
    
    def calculate_houses(self, birth_date: date, birth_time: time, timezone_str: str, latitude: float, longitude: float):
        """Calculates the 12 House cusps and core angles safely using zero-indexed array structures."""
        julian_day = self._convert_to_utc_julian_day(birth_date, birth_time, timezone_str)
        
        # Call houses_ex using the Placidus byte standard (b'P')
        house_data = swe.houses_ex(julian_day, latitude, longitude, b'P')
        
        # Extract tuples directly
        cusps = house_data[0]
        ascmc = house_data[1]
        
        ascendant_long = ascmc[0]
        midheaven_long = ascmc[1]
        
        # Format the 12 house cusps shifting to 0-based tuple positions (Index 0 = House 1)
        houses_data = {}
        for i in range(1, 13):
            house_long = cusps[i - 1]  # Maps house 1 to index 0, house 12 to index 11
            houses_data[f"House_{i}"] = {
                "absolute_degree": round(house_long, 4),
                "zodiac_sign": self._get_zodiac_sign(house_long)
            }
            
        return {
            "angles": {
                "Ascendant": {
                    "absolute_degree": round(ascendant_long, 4),
                    "zodiac_sign": self._get_zodiac_sign(ascendant_long)
                },
                "Midheaven": {
                    "absolute_degree": round(midheaven_long, 4),
                    "zodiac_sign": self._get_zodiac_sign(midheaven_long)
                }
            },
            "houses": houses_data
        }