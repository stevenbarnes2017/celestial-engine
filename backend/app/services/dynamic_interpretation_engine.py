import os
from groq import Groq
from datetime import datetime

class DynamicInterpretationEngine:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    # ========================================================================
    # WESTERN ASTROLOGY READINGS
    # ========================================================================

    def generate_western_daily(self, sign, transits, date_obj):
        """Generate daily Western horoscope for a specific sign"""
        if not self.client:
            return self._offline_message()

        # Format transits
        transit_text = self._format_transits(transits)
        
        system_prompt = (
            "You are a professional Western astrologer writing daily horoscopes. "
            "Create an engaging, authentic daily horoscope for the specified zodiac sign. "
            "Use current planetary transits to inform your reading. Focus on practical guidance, "
            "emotional insights, and opportunities for the day. Write in a warm, insightful tone. "
            "Structure: **Today's Energy** (overview), **Opportunities** (what to pursue), "
            "**Challenges** (what to watch for), **Focus Areas** (key themes). "
            "Keep it conversational and helpful, around 200-250 words."
        )

        user_prompt = (
            f"Write a daily horoscope for {sign} on {date_obj.strftime('%A, %B %d, %Y')}.\n\n"
            f"Active Transits:\n{transit_text}\n\n"
            f"Create an authentic, helpful daily reading."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=512)

    def generate_western_weekly(self, sign, week_start, week_end):
        """Generate weekly Western horoscope"""
        if not self.client:
            return self._offline_message()

        system_prompt = (
            "You are a professional Western astrologer writing weekly horoscopes. "
            "Create an insightful weekly forecast for the specified zodiac sign. "
            "Cover the major themes, opportunities, and challenges for the week ahead. "
            "Structure: **Week Overview**, **Love & Relationships**, **Career & Finance**, "
            "**Health & Wellness**, **Key Days** (highlight 2-3 important days). "
            "Write in an engaging, supportive tone. Around 300-350 words."
        )

        user_prompt = (
            f"Write a weekly horoscope for {sign} covering "
            f"{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}.\n\n"
            f"Provide a comprehensive weekly forecast."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=768)

    def generate_western_monthly(self, sign, month_start):
        """Generate monthly Western horoscope"""
        if not self.client:
            return self._offline_message()

        month_name = month_start.strftime('%B %Y')

        system_prompt = (
            "You are an expert Western astrologer writing monthly horoscopes. "
            "Create a detailed monthly forecast for the specified zodiac sign. "
            "Cover major planetary movements, eclipses (if any), and key themes for the month. "
            "Structure: **Monthly Overview**, **Love & Relationships**, **Career & Ambitions**, "
            "**Money & Resources**, **Health & Self-Care**, **Important Dates**. "
            "Write with depth and insight. Around 400-500 words."
        )

        user_prompt = (
            f"Write a comprehensive monthly horoscope for {sign} for {month_name}.\n\n"
            f"Provide detailed insights and guidance for the entire month."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=1024)

    def generate_western_yearly(self, sign, year):
        """Generate yearly Western horoscope"""
        if not self.client:
            return self._offline_message()

        system_prompt = (
            "You are a master Western astrologer writing annual forecasts. "
            "Create an in-depth yearly horoscope for the specified zodiac sign. "
            "Cover major themes, growth areas, and significant planetary transits throughout the year. "
            "Structure: **Year Overview**, **Personal Growth**, **Love & Relationships**, "
            "**Career & Success**, **Health & Wellbeing**, **Spiritual Development**, "
            "**Key Months** (highlight 3-4 pivotal months). "
            "Write with wisdom and foresight. Around 600-700 words."
        )

        user_prompt = (
            f"Write a comprehensive yearly horoscope for {sign} for {year}.\n\n"
            f"Provide an insightful, detailed forecast for the entire year."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=1536)

    # ========================================================================
    # CHINESE ZODIAC READINGS
    # ========================================================================

    def generate_chinese_daily(self, animal_sign, date_obj):
        """Generate daily Chinese zodiac horoscope"""
        if not self.client:
            return self._offline_message()

        system_prompt = (
            "You are an expert in Chinese astrology and the zodiac animals. "
            "Write daily horoscopes based on the Chinese zodiac system. "
            "Consider the animal's inherent characteristics, elemental influences, and "
            "the current day's energy based on the Chinese calendar principles. "
            "Structure: **Today's Chi** (energy overview), **Lucky Elements** (colors, directions, numbers), "
            "**Opportunities**, **Cautions**. Keep it practical and culturally authentic. Around 200-250 words."
        )

        user_prompt = (
            f"Write a daily Chinese zodiac horoscope for people born in the Year of the {animal_sign} "
            f"on {date_obj.strftime('%A, %B %d, %Y')}.\n\n"
            f"Provide authentic Chinese astrology insights."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=512)

    def generate_chinese_weekly(self, animal_sign, week_start, week_end):
        """Generate weekly Chinese zodiac horoscope"""
        if not self.client:
            return self._offline_message()

        system_prompt = (
            "You are a master of Chinese astrology and fortune telling. "
            "Write weekly forecasts based on the Chinese zodiac system. "
            "Consider the Five Elements (Wood, Fire, Earth, Metal, Water), yin-yang balance, "
            "and the animal's characteristics. Structure: **Week's Energy**, **Career & Money**, "
            "**Relationships**, **Health**, **Lucky Days**. Around 300-350 words."
        )

        user_prompt = (
            f"Write a weekly Chinese zodiac forecast for the {animal_sign} covering "
            f"{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=768)

    def generate_chinese_monthly(self, animal_sign, month_start):
        """Generate monthly Chinese zodiac horoscope"""
        if not self.client:
            return self._offline_message()

        month_name = month_start.strftime('%B %Y')

        system_prompt = (
            "You are an expert Chinese astrologer and Feng Shui master. "
            "Write monthly forecasts based on Chinese zodiac and elemental theory. "
            "Consider the monthly Earthly Branch, Flying Stars if relevant, and Five Element interactions. "
            "Structure: **Monthly Overview**, **Wealth & Career**, **Love & Family**, "
            "**Health & Vitality**, **Feng Shui Tips**, **Auspicious Dates**. Around 400-500 words."
        )

        user_prompt = (
            f"Write a comprehensive Chinese zodiac monthly forecast for the {animal_sign} "
            f"for {month_name}."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=1024)

    def generate_chinese_yearly(self, animal_sign, year):
        """Generate yearly Chinese zodiac horoscope"""
        if not self.client:
            return self._offline_message()

        system_prompt = (
            "You are a revered Chinese astrology master with deep knowledge of the Chinese zodiac, "
            "BaZi (Four Pillars), and traditional fortune telling. "
            "Write comprehensive annual forecasts based on the animal sign and the year's ruling energy. "
            "Structure: **Year Overview** (relationship with year's ruling animal), **Career & Wealth Fortune**, "
            "**Love & Relationships**, **Health & Wellbeing**, **Personal Development**, "
            "**Auspicious Months**, **Feng Shui Recommendations**. Around 600-700 words."
        )

        user_prompt = (
            f"Write a comprehensive Chinese zodiac yearly forecast for people born in the Year of the {animal_sign} "
            f"for the year {year}."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=1536)

    # ========================================================================
    # PERSONALIZED READING (with natal chart)
    # ========================================================================

    def synthesize_chart_manifest(self, user_record):
        """Flattens stored database blocks into an information-dense text manifest."""
        planets = user_record.planetary_positions or {}
        aspects = user_record.planetary_aspects or []
        bazi = user_record.bazi_pillars or {}

        # 1. Western Geometry
        western_manifest = "WESTERN NATAL GEOMETRY:\n"
        for planet, data in planets.items():
            western_manifest += f"- {planet}: {data['absolute_degree']}° in {data['zodiac_sign']}\n"
        
        # 2. Geometric Aspects
        aspect_manifest = "\nCALCULATED GEOMETRIC ASPECTS:\n"
        for asp in aspects:
            aspect_manifest += (
                f"- {asp['planet_a']} {asp['aspect']} {asp['planet_b']} "
                f"(Distance: {asp['angular_distance']}°, Orb: {asp['orb_variance']}°)\n"
            )

        # 3. Eastern Four Pillars
        bazi_manifest = "\nEASTERN FOUR PILLARS MATRIX:\n"
        for pillar in ["Year_Pillar", "Month_Pillar", "Day_Pillar", "Hour_Pillar"]:
            if pillar in bazi:
                bazi_manifest += f"- {pillar}: {bazi[pillar]['Stem']} (Stem) over {bazi[pillar]['Branch']} (Branch)\n"
        
        if "meta" in bazi:
            bazi_manifest += f"- True Solar Hour: {bazi['meta'].get('true_solar_hour_decimal')}\n"

        return f"{western_manifest}{aspect_manifest}{bazi_manifest}"

    def generate_authentic_horoscope(self, user_record):
        """
        Generates personalized natal chart interpretation combining Western and Eastern systems
        """
        if not self.client:
            return self._offline_message()

        chart_data = self.synthesize_chart_manifest(user_record)

        system_prompt = (
            "You are an elite astrologer specializing in both Western Evolutionary Astrology "
            "and traditional Eastern BaZi (Four Pillars of Destiny). Provide an authentic, "
            "integrated reading based on the mathematical data provided. Synthesize how Western "
            "placements and Eastern elements interact. Structure: **Core Essence**, "
            "**Psychological Dynamics**, **Elemental Alignment**, **Life Path Insights**. "
            "Write with depth and professionalism. Around 400-500 words."
        )

        user_prompt = f"Interpret this natal chart:\n\n{chart_data}"

        return self._generate_reading(system_prompt, user_prompt, max_tokens=1024)

    def generate_daily_horoscope(self, user_record, active_transits):
        """
        Personalized daily horoscope using natal chart + current transits
        """
        if not self.client:
            return "Groq Engine Offline: Cannot synthesize transit matrices."

        # Format transits
        transit_text = self._format_transits(active_transits)
        
        # Get baseline data
        bazi = user_record.bazi_pillars or {}
        day_master = bazi.get("Day_Pillar", {}).get("Stem", "Unknown")
        
        planets = user_record.planetary_positions or {}
        sun_sign = planets.get("Sun", {}).get("zodiac_sign", "Unknown")

        system_prompt = (
            "You are a master evolutionary astrologer writing personalized daily horoscopes. "
            "Use the person's natal chart signatures and current transits to create an authentic forecast. "
            "Focus on psychological atmospheres, timing, and emotional landscapes. "
            "Structure: **Today's Vibe**, **Core Opportunities**, **Potential Blindspots**. "
            "Around 250-300 words."
        )

        user_prompt = (
            f"Profile: {day_master} Day Master, Sun in {sun_sign}\n\n"
            f"Active Transits:\n{transit_text}\n\n"
            f"Generate today's personalized horoscope."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=640)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _format_transits(self, transits):
        """Format transit list into readable text"""
        if not transits:
            return "- No major transits active today"
        
        transit_lines = []
        for t in transits:
            transit_lines.append(
                f"- {t.get('transit_planet', 'Unknown')} {t.get('aspect', '')} "
                f"{t.get('natal_planet', 'Unknown')} (Orb: {t.get('orb_variance', '?')}°)"
            )
        return "\n".join(transit_lines)

    def _generate_reading(self, system_prompt, user_prompt, max_tokens=512):
        """Core reading generation with error handling"""
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating reading: {str(e)}"

    def _offline_message(self):
        """Return when Groq API is unavailable"""
        return (
            "Interpretation Engine Offline: GROQ_API_KEY environment variable is missing. "
            "Please configure your API key to enable AI-powered readings."
        )

    def generate_sky_interpretation(self, current_positions, date_obj):
        """
        Generate interpretation of current planetary configuration
        """
        if not self.client:
            return self._offline_message()

        # Format planetary positions
        positions_text = "CURRENT PLANETARY POSITIONS:\n"
        for planet, data in current_positions.items():
            positions_text += f"- {planet}: {data['absolute_degree']:.2f}° in {data['zodiac_sign']}\n"

        system_prompt = (
            "You are a master astrologer explaining the current cosmic weather to the general public. "
            "Based on the current planetary positions, describe the overall energy and themes present today. "
            "Focus on the collective mood, opportunities, and challenges that everyone might feel. "
            "Structure: **Current Cosmic Climate** (overall feel), **Planetary Highlights** (notable positions), "
            "**Collective Energy** (what's in the air), **Suggested Focus** (how to work with today's energy). "
            "Write in an accessible, inspiring tone. Around 300-350 words."
        )

        user_prompt = (
            f"Today's Date: {date_obj.strftime('%A, %B %d, %Y')}\n\n"
            f"{positions_text}\n\n"
            f"Interpret today's celestial configuration for a general audience."
        )

        return self._generate_reading(system_prompt, user_prompt, max_tokens=768)