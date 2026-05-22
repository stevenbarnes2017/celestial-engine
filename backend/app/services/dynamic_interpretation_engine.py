import os
from groq import Groq

class DynamicInterpretationEngine:
    def __init__(self):
        # Ingests the GROQ_API_KEY from your local environment
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def synthesize_chart_manifest(self, user_record) -> str:
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
                f"(Distance: {asp['angular_distance']}°, Orb Variance: {asp['orb_variance']}°)\n"
            )

        # 3. Eastern Four Pillars
        bazi_manifest = "\nEASTERN FOUR PILLARS MATRIX:\n"
        for pillar in ["Year_Pillar", "Month_Pillar", "Day_Pillar", "Hour_Pillar"]:
            if pillar in bazi:
                bazi_manifest += f"- {pillar}: {bazi[pillar]['Stem']} (Stem) over {bazi[pillar]['Branch']} (Branch)\n"
        
        if "meta" in bazi:
            bazi_manifest += f"- True Solar Hour Decimal: {bazi['meta'].get('true_solar_hour_decimal')}\n"

        return f"{western_manifest}{aspect_manifest}{bazi_manifest}"

    def generate_authentic_horoscope(self, user_record) -> str:
        """
        Sends the mathematical chart manifest to Groq, running it through 
        Llama-3-70b for instantaneous, authentic multi-system synthesis.
        """
        if not self.client:
            return (
                "Groq Interpretation Engine is offline: GROQ_API_KEY environment "
                "variable is missing. Please review your server keys."
            )

        chart_data_summary = self.synthesize_chart_manifest(user_record)

        system_instruction = (
            "You are an elite, multi-disciplinary astrologer specializing in both Western Evolutionary "
            "Astrology and traditional Eastern BaZi (Four Pillars of Destiny). Your task is to provide an "
            "authentic, highly integrated, and deeply insightful reading based on the raw mathematical data "
            "provided. Do not merely spit the raw degrees back out. Instead, synthesize how the different layers "
            "interact—for instance, how a user's Western natal placements or intense geometric clusters (like tight "
            "conjunctions or trines) reflect or modify their Eastern Day Master identity. Keep your tone "
            "grounded, professional, and sophisticated. Deliver the reading in clear paragraphs split by "
            "logical sections (e.g., Core Essence, Psychological Dynamics, and Elemental Alignment)."
        )

        try:
            # Swapping to Llama 3.3 70B for high-speed, advanced astrological reasoning
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # <-- UPDATE THIS STRING
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction
                    },
                    {
                        "role": "user",
                        "content": f"Please interpret this specific natal data map:\n\n{chart_data_summary}"
                    }
                ],
                temperature=0.7,
                max_tokens=2048
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error executing authentic Groq LPU synthesis: {str(e)}"
        
    def generate_daily_horoscope(self, user_record, active_transits) -> str:
        """
        Synthesizes moving transits against the user's permanent profile data
        to write a high-speed, hyper-personalized 24-hour forecast via Groq.
        """
        if not self.client:
            return "Groq Engine Offline: Cannot synthesize transit matrices."

        # 1. Format the active transits into a readable context block
        transit_manifest = "ACTIVE DAILY TRANSITS (Current Sky hitting Natal Chart):\n"
        if not active_transits:
            transit_manifest += "- No major geometric alignments hitting the chart today. Minor elemental flows dominate.\n"
        for t in active_transits:
            transit_manifest += (
                f"- Today's Moving {t['transit_planet']} forms a temporary {t['aspect']} "
                f"to Natal {t['natal_planet']} (Orb: {t['orb_variance']}°)\n"
            )

        # 2. Grab core baseline signatures for context
        bazi = user_record.bazi_pillars or {}
        day_master = bazi.get("Day_Pillar", {}).get("Stem", "Unknown Master")

        system_instruction = (
            "You are a master evolutionary astrologer writing a highly authentic daily horoscope. "
            "You will be given a list of active transits representing how the current sky is triggering the user's birth chart today. "
            "Interpret what these temporary energetic intersections mean for their day ahead. Focus heavily on psychological "
            "atmospheres, timing, productivity gates, and emotional landscapes. Do not read out raw math parameters; write a cohesive, "
            "deeply engaging daily forecast split into paragraphs: Today's Vibe, Core Opportunities, and Potential Blindspots."
        )

        user_prompt = (
            f"User Profile Baseline: Yang Earth Day Master. Western Sun in Pisces.\n\n"
            f"{transit_manifest}\n"
            f"Please generate today's live personalized daily horoscope layout."
        )

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error compounding dynamic daily transits: {str(e)}"