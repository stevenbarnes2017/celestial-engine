class AspectEngine:
    def __init__(self):
        # Define the major aspects, their target angles, and allowed variance (orbs)
        self.ASPECT_DEFINITIONS = {
            "Conjunction": {"target": 0, "orb": 8},
            "Sextile": {"target": 60, "orb": 6},
            "Square": {"target": 90, "orb": 8},
            "Trine": {"target": 120, "orb": 8},
            "Opposition": {"target": 180, "orb": 8}
        }

    def calculate_aspects(self, planetary_positions: dict) -> list:
        """
        Scans a dictionary of planetary positions, calculates the shortest angular 
        distance between every pair, and returns matching geometric aspects.
        """
        aspects_found = []
        planets_list = list(planetary_positions.keys())
        num_planets = len(planets_list)

        # Matrix scan comparison loop (prevents duplicating planet_a vs planet_b)
        for i in range(num_planets):
            for j in range(i + 1, num_planets):
                p1 = planets_list[i]
                p2 = planets_list[j]

                deg1 = planetary_positions[p1]["absolute_degree"]
                deg2 = planetary_positions[p2]["absolute_degree"]

                # Calculate the shortest angular distance on a 360-degree circle
                diff = abs(deg1 - deg2)
                angular_distance = diff if diff <= 180 else 360 - diff

                # Check our distance against aspect definitions
                for aspect_name, config in self.ASPECT_DEFINITIONS.items():
                    target = config["target"]
                    max_orb = config["orb"]

                    # Determine variance from the exact aspect angle
                    current_orb = abs(angular_distance - target)

                    if current_orb <= max_orb:
                        aspects_found.append({
                            "planet_a": p1,
                            "planet_b": p2,
                            "aspect": aspect_name,
                            "angular_distance": round(angular_distance, 4),
                            "exact_angle": target,
                            "orb_variance": round(current_orb, 4)
                        })
                        break # An angular distance can only match one aspect type

        return aspects_found