import os
import swisseph as swe
from datetime import datetime, date, time
import pytz

class BaziEngine:
    def __init__(self):
        # Point to our existing ephemeris directory for high-precision sun tracking
        ephe_path = os.path.join(os.path.dirname(__file__), 'ephe')
        swe.set_ephe_path(ephe_path)

        # 10 Heavenly Stems (Yang/Yin + Five Elements)
        self.STEMS = ["Yang Wood", "Yin Wood", "Yang Fire", "Yin Fire", 
                      "Yang Earth", "Yin Earth", "Yang Metal", "Yin Metal", 
                      "Yang Water", "Yin Water"]

        # 12 Earthly Branches (Zodiac Animals)
        self.BRANCHES = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", 
                         "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]

    def _get_julian_day(self, birth_date: date, birth_time: time, timezone_str: str) -> float:
        """Converts telemetry to Julian Day."""
        local_tz = pytz.timezone(timezone_str)
        naive_dt = datetime.combine(birth_date, birth_time)
        localized_dt = local_tz.localize(naive_dt)
        utc_dt = localized_dt.astimezone(pytz.utc)
        
        decimal_utc_hour = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)
        return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_utc_hour)

    def calculate_bazi(self, birth_date: date, birth_time: time, timezone_str: str, longitude: float):
        """Computes the Four Pillars (Year, Month, Day, Hour) based on Solar Terms."""
        jd = self._get_julian_day(birth_date, birth_time, timezone_str)
        
        # 1. Fetch exact Sun Longitude to determine Solar Terms (Crucial for Month boundaries)
        sun_res, _ = swe.calc_ut(jd, swe.SUN, 0)
        sun_long = sun_res[0]

        # 2. Year Pillar Calculation
        # The Chinese Solar Year starts at Lichun (Spring Begins, precisely at 315° Sun Longitude)
        # We find the baseline year cycle anchor relative to the Jia-Zi epoch
        base_year = birth_date.year
        if sun_long < 315 and birth_date.month <= 3:
            # If born before Lichun (usually Feb 4), they belong to the previous solar year
            base_year -= 1
            
        year_index = (base_year - 4) % 60
        year_stem = self.STEMS[year_index % 10]
        year_branch = self.BRANCHES[year_index % 12]

        # 3. Month Pillar Calculation
        # Month pillars switch exactly on 12 distinct Solar Terms (30-degree increments starting from 315°)
        # Shift 315° to 0° baseline to calculate the current solar month index (0 to 11)
        adjusted_sun_long = (sun_long - 315) % 360
        solar_month_index = int(adjusted_sun_long // 30)
        
        # Earthly branch of the first solar month (Lichun) is always the Tiger
        month_branch_index = (solar_month_index + 2) % 12
        month_branch = self.BRANCHES[month_branch_index]
        
        # The Month Stem is programmatically derived from the Year Stem baseline
        year_stem_index = year_index % 10
        month_stem_start = (year_stem_index % 5) * 2 + 2
        month_stem_index = (month_stem_start + solar_month_index) % 10
        month_stem = self.STEMS[month_stem_index]

        # 4. Day Pillar Calculation
        # Expressed directly as an unbroken sequence from a known historical Jia-Zi day anchor
        # Julian Day 2440588.5 is Jan 1, 1970, which happened to be a Gui-Si day (Stem index 9, Branch index 5)
        jd_midnight = int(jd + 0.5) - 0.5  # Standardize to local calendar day boundary
        day_offset = int(jd_midnight - 2440587.5)
        day_index = (day_offset + 49) % 60  # Anchor index shifting
        
        day_stem = self.STEMS[day_index % 10]
        day_branch = self.BRANCHES[day_index % 12]

        # 5. Hour Pillar Calculation
        # Chinese hours use 12 two-hour double-hours (True Solar Time adjustments applied via longitude)
        # Calculate local mean solar time offset from UTC
        raw_hours = birth_time.hour + (birth_time.minute / 60.0)
        solar_time_adjustment = longitude / 15.0  # 15 degrees longitude = 1 hour time shift
        
        # Calculate timezone standard offset
        local_tz = pytz.timezone(timezone_str)
        naive_dt = datetime.combine(birth_date, birth_time)
        tz_offset_hours = local_tz.localize(naive_dt).utcoffset().total_seconds() / 3600.0
        
        true_solar_hour = (raw_hours - tz_offset_hours + solar_time_adjustment) % 24
        
        # Map 24 hours into 12 Earthly Branches (Rat begins at 23:00 / 11 PM of the previous night)
        hour_branch_index = int((true_solar_hour + 1) % 24 // 2)
        hour_branch = self.BRANCHES[hour_branch_index]
        
        # Hour Stem is derived directly from the Day Stem baseline
        day_stem_index = day_index % 10
        hour_stem_start = (day_stem_index % 5) * 2
        hour_stem_index = (hour_stem_start + hour_branch_index) % 10
        hour_stem = self.STEMS[hour_stem_index]

        return {
            "Year_Pillar": {"Stem": year_stem, "Branch": year_branch},
            "Month_Pillar": {"Stem": month_stem, "Branch": month_branch},
            "Day_Pillar": {"Stem": day_stem, "Branch": day_branch},
            "Hour_Pillar": {"Stem": hour_stem, "Branch": hour_branch},
            "meta": {
                "calculated_sun_longitude": round(sun_long, 4),
                "true_solar_hour_decimal": round(true_solar_hour, 2)
            }
        }