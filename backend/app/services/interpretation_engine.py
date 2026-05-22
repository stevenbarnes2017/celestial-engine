class InterpretationEngine:
    def __init__(self):
        # Semantic mapping tables for core natal placements
        self.PLANET_SIGN_TEXT = {
            "Sun": {
                "Pisces": "Your core identity is deeply intuitive, empathetic, and imaginative. You navigate life through emotional and spiritual wavelengths, processing the world via subtle undercurrents rather than hard boundaries.",
                "default": "Your solar core illuminates your primary driving force."
            },
            "Moon": {
                "Taurus": "Emotionally, you seek stability, comfort, and predictability. You possess a deeply grounded emotional nature that processes feelings through physical senses and steady, deliberate routines.",
                "default": "Your lunar profile dictates your internal emotional landscape."
            }
        }

        # Semantic mapping tables for planetary aspect interactions
        self.ASPECT_TEXT = {
            "Mars": {
                "Saturn": {
                    "Conjunction": "Mars conjunct Saturn creates an intense structural engine within you. Your raw ambition, drive, and impulse (Mars) are tightly bound by discipline, caution, and systemic boundaries (Saturn). This manifests as a master strategist—someone who can endure immense pressure and channel high-energy output into highly controlled, long-term achievements."
                }
            }
        }

        # Semantic mapping tables for Eastern BaZi elements
        self.BAZI_TEXT = {
            "Day_Pillar": {
                "Stem": {
                    "Yang Earth": "Your Day Master is Yang Earth, symbolizing a mountain. You are naturally stable, supportive, and reliable. You stand firm in your convictions and act as a solid foundation for those around you, though you must watch for a tendency toward stubbornness or resisting necessary change."
                }
            }
        }

    def generate_horoscope(self, user_record) -> dict:
        """
        Parses a user's calculated astronomical database arrays and compiles
        a semantic, human-readable horoscope delineation block.
        """
        planets = user_record.planetary_positions or {}
        aspects = user_record.planetary_aspects or []
        bazi = user_record.bazi_pillars or {}

        interpretations = {
            "placements": [],
            "dynamics": [],
            "eastern_core": []
        }

        # 1. Parse Key Placements (Sun & Moon)
        for body in ["Sun", "Moon"]:
            if body in planets:
                sign = planets[body]["zodiac_sign"]
                text = self.PLANET_SIGN_TEXT.get(body, {}).get(sign, self.PLANET_SIGN_TEXT.get(body, {}).get("default", ""))
                interpretations["placements"].append({
                    "title": f"{body} in {sign}",
                    "delineation": text
                })

        # 2. Parse High-Priority Aspects (Looking for that exact Mars-Saturn cluster)
        for asp in aspects:
            p_a = asp["planet_a"]
            p_b = asp["planet_b"]
            asp_type = asp["aspect"]

            # Check for mapping definitions in both directional combinations
            text = (self.ASPECT_TEXT.get(p_a, {}).get(p_b, {}).get(asp_type) or 
                    self.ASPECT_TEXT.get(p_b, {}).get(p_a, {}).get(asp_type))
            
            if text:
                interpretations["dynamics"].append({
                    "title": f"{p_a} {asp_type} {p_b}",
                    "delineation": text
                })

        # 3. Parse Eastern Day Master Core Attributes
        if "Day_Pillar" in bazi:
            day_stem = bazi["Day_Pillar"].get("Stem")
            bazi_text = self.BAZI_TEXT["Day_Pillar"]["Stem"].get(day_stem)
            if bazi_text:
                interpretations["eastern_core"].append({
                    "title": f"Day Master: {day_stem}",
                    "delineation": bazi_text
                })

        return interpretations