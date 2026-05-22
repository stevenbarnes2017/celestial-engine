import math

class TransitEngine:
    def __init__(self):
        # Define traditional major aspect angles for transit tracking
        self.ASPECTS = {
            "Conjunction": {"angle": 0, "orb": 5.0},
            "Sextile": {"angle": 60, "orb": 4.0},
            "Square": {"angle": 90, "orb": 5.0},
            "Trine": {"angle": 120, "orb": 6.0},
            "Opposition": {"angle": 180, "orb": 5.0}
        }

    def calculate_transit_aspects(self, natal_planets, current_sky_planets) -> list:
        """
        Compares moving current planetary degrees against permanent natal degrees
        to find active temporary aspects shaping the user's current day.
        """
        active_transits = []

        for current_planet, current_data in current_sky_planets.items():
            curr_deg = current_data["absolute_degree"]
            
            for natal_planet, natal_data in natal_planets.items():
                nat_deg = natal_data["absolute_degree"]
                
                # Calculate the shortest angular distance on a 360-degree wheel
                diff = abs(curr_deg - nat_deg)
                distance = diff if diff <= 180 else 360 - diff
                
                # Check against our transit aspect rules
                for aspect_name, rules in self.ASPECTS.items():
                    target_angle = rules["angle"]
                    max_orb = rules["orb"]
                    
                    orb_variance = abs(distance - target_angle)
                    if orb_variance <= max_orb:
                        active_transits.append({
                            "transit_planet": current_planet,
                            "aspect": aspect_name,
                            "natal_planet": natal_planet,
                            "angular_distance": round(distance, 4),
                            "orb_variance": round(orb_variance, 4)
                        })
                        
        return active_transits