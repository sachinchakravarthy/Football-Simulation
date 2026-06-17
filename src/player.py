import pygame
import math
import random

class Player:
    def __init__(self, x, y, team, name, role, color, radius=10):
        self.x = x
        self.y = y
        self.home_x = x  # Original position for formation
        self.home_y = y
        self.team = team
        self.name = name
        self.role = role
        self.color = color
        self.radius = radius

        # Movement properties
        self.velocity_x = 0
        self.velocity_y = 0
        self.max_speed = 2.0
        self.acceleration = 0.3
        self.friction = 0.85

        # AI properties
        self.state = "positioning"  # positioning, chasing, supporting
        self.target_x = x
        self.target_y = y
        self.decision_timer = 0
        self.last_decision_time = 0

        # Role-based attributes
        self.set_role_attributes()

    def set_role_attributes(self):
        """Set attributes based on player role"""
        if self.role == "GK":
            self.max_speed = 1.5
            self.tackle_range = 25
            self.support_range = 100
        elif self.role in ["CB", "LB", "RB"]:
            self.max_speed = 1.8
            self.tackle_range = 20
            self.support_range = 120
        elif self.role in ["CM", "LM", "RM"]:
            self.max_speed = 2.2
            self.tackle_range = 18
            self.support_range = 140
        elif self.role in ["LW", "RW", "ST"]:
            self.max_speed = 2.5
            self.tackle_range = 15
            self.support_range = 130

    def update(self, dt):
        """Update player position with smooth movement"""
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction

        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Keep within field bounds
        self.x = max(10, min(790, self.x))
        self.y = max(10, min(590, self.y))

        # Update decision timer
        self.decision_timer += dt

    def move_towards(self, target_x, target_y, urgency=1.0):
        """Smooth movement towards a target with momentum"""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance > 5:  # Don't micro-adjust
            # Normalize direction
            if distance > 0:
                dir_x = dx / distance
                dir_y = dy / distance

                # Calculate desired velocity
                desired_speed = min(self.max_speed * urgency, distance * 0.1)
                desired_vel_x = dir_x * desired_speed
                desired_vel_y = dir_y * desired_speed

                # Smoothly adjust velocity
                self.velocity_x += (desired_vel_x - self.velocity_x) * self.acceleration
                self.velocity_y += (desired_vel_y - self.velocity_y) * self.acceleration

    def draw(self, screen):
        # Draw player as colored circle with better visibility
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

        # Draw role text above player
        font = pygame.font.SysFont(None, 14)
        text = font.render(self.role, True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(self.x), int(self.y - 18)))
        screen.blit(text, text_rect)

        # Draw state indicator (small dot)
        state_colors = {
            "chasing": (255, 255, 0),    # Yellow
            "supporting": (0, 255, 0),   # Green  
            "positioning": (128, 128, 128)  # Gray
        }
        if self.state in state_colors:
            pygame.draw.circle(screen, state_colors[self.state], 
                             (int(self.x + 8), int(self.y - 8)), 3)

    def decide_action(self, ball, all_players, dt):
        """Make decisions about what to do"""
        # Only make decisions every 200ms to avoid jittery behavior
        if self.decision_timer < 200:
            return

        self.decision_timer = 0

        ball_distance = math.hypot(ball.x - self.x, ball.y - self.y)

        # Find teammates and opponents
        teammates = [p for p in all_players if p.team == self.team and p != self]
        opponents = [p for p in all_players if p.team != self.team]

        # Determine closest player to ball
        closest_to_ball = min(all_players, key=lambda p: math.hypot(ball.x - p.x, ball.y - p.y))

        # Decision logic
        if closest_to_ball == self:
            self.state = "chasing"
            self.target_x = ball.x
            self.target_y = ball.y
        else:
            # Check if we should support
            if ball_distance < self.support_range and self.should_support(ball, teammates):
                self.state = "supporting"
                self.calculate_support_position(ball, closest_to_ball)
            else:
                self.state = "positioning"
                # Move towards formation position with some variation
                offset_x = random.uniform(-20, 20)
                offset_y = random.uniform(-20, 20)
                self.target_x = self.home_x + offset_x
                self.target_y = self.home_y + offset_y

    def should_support(self, ball, teammates):
        """Decide if player should move to support"""
        # Attackers are more likely to support in attack
        if self.role in ["ST", "LW", "RW"]:
            if self.team == "A" and ball.x > 300:
                return random.random() < 0.7
            elif self.team == "B" and ball.x < 500:
                return random.random() < 0.7

        # Midfielders support more generally
        elif self.role in ["CM", "LM", "RM"]:
            return random.random() < 0.5

        # Defenders support when defending
        elif self.role in ["CB", "LB", "RB"]:
            if self.team == "A" and ball.x < 400:
                return random.random() < 0.6
            elif self.team == "B" and ball.x > 400:
                return random.random() < 0.6

        return False

    def calculate_support_position(self, ball, ball_carrier):
        """Calculate good support position"""
        if ball_carrier and ball_carrier.team == self.team:
            # Position for pass reception
            if self.team == "A":
                # Move forward and to the side
                self.target_x = ball.x + random.uniform(30, 80)
                self.target_y = ball.y + random.uniform(-60, 60)
            else:
                self.target_x = ball.x - random.uniform(30, 80)
                self.target_y = ball.y + random.uniform(-60, 60)
        else:
            # Defensive positioning
            goal_x = 50 if self.team == "A" else 750
            # Position between ball and goal
            self.target_x = (ball.x + goal_x) / 2
            self.target_y = (ball.y + 300) / 2

    def update_movement(self, dt):
        """Update player movement towards target"""
        urgency = 1.0
        if self.state == "chasing":
            urgency = 1.2
        elif self.state == "supporting":
            urgency = 0.8
        else:  # positioning
            urgency = 0.6

        self.move_towards(self.target_x, self.target_y, urgency)

    def can_see(self, target_player):
        """Improved line of sight calculation"""
        dx = target_player.x - self.x
        dy = target_player.y - self.y
        distance = math.hypot(dx, dy)

        # Can't see if too far
        if distance > 180:
            return False

        # Add some randomness to make it feel more realistic
        visibility_chance = max(0.3, 1.0 - distance / 200.0)
        return random.random() < visibility_chance

    def attempt_tackle(self, opponent):
        """Improved tackling with better success rates"""
        dx = opponent.x - self.x
        dy = opponent.y - self.y
        distance = math.hypot(dx, dy)

        if distance <= self.tackle_range:
            # Base success rate
            base_success = 0.15

            # Role-based modifiers
            if self.role in ["CB", "LB", "RB"]:
                base_success = 0.25
            elif self.role in ["CM", "LM", "RM"]:
                base_success = 0.20
            elif self.role == "GK":
                base_success = 0.35

            # Distance modifier (closer = better)
            distance_modifier = (self.tackle_range - distance) / self.tackle_range
            final_success = base_success + (distance_modifier * 0.15)

            return random.random() < final_success

        return False

    def reset_position(self):
        """Reset to home position"""
        self.x = self.home_x
        self.y = self.home_y
        self.velocity_x = 0
        self.velocity_y = 0
        self.state = "positioning"
        self.target_x = self.home_x
        self.target_y = self.home_y
