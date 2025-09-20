def formation_433(team_side):
    """
    4-3-3 Formation setup
    team_side: "left" or "right"
    Returns list of (role, x, y) for player positions
    """
    positions = [
        ("GK", 0, 300),     # Goalkeeper
        ("LB", 50, 150),    # Left Back
        ("CB", 50, 250),    # Center Back 1
        ("CB", 50, 350),    # Center Back 2
        ("RB", 50, 450),    # Right Back
        ("LM", 150, 180),   # Left Midfielder
        ("CM", 150, 300),   # Center Midfielder
        ("RM", 150, 420),   # Right Midfielder
        ("LW", 250, 150),   # Left Winger
        ("ST", 250, 300),   # Striker
        ("RW", 250, 450),   # Right Winger
    ]

    if team_side == "left":
        return [(role, x + 50, y) for role, x, y in positions]
    elif team_side == "right":
        # Flip X-axis across the midline (800px field width)
        return [(role, 800 - x - 50, y) for role, x, y in positions]

def formation_442(team_side):
    """
    4-4-2 Formation setup - Alternative formation
    """
    positions = [
        ("GK", 0, 300),     # Goalkeeper
        ("LB", 50, 130),    # Left Back
        ("CB", 50, 230),    # Center Back 1
        ("CB", 50, 370),    # Center Back 2
        ("RB", 50, 470),    # Right Back
        ("LM", 150, 150),   # Left Midfielder
        ("CM", 150, 250),   # Center Midfielder 1
        ("CM", 150, 350),   # Center Midfielder 2
        ("RM", 150, 450),   # Right Midfielder
        ("ST", 250, 250),   # Striker 1
        ("ST", 250, 350),   # Striker 2
    ]

    if team_side == "left":
        return [(role, x + 50, y) for role, x, y in positions]
    elif team_side == "right":
        return [(role, 800 - x - 50, y) for role, x, y in positions]
