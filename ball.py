import pygame
import math

class Ball:
    def __init__(self, x, y, radius=8, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.velocity = [0, 0]
        self.last_passer = None

        # Physics properties
        self.friction = 0.98
        self.bounce_damping = 0.7
        self.min_velocity = 0.1

    def draw(self, screen):
        # Draw ball with shadow effect
        shadow_offset = 3
        pygame.draw.circle(screen, (100, 100, 100), 
                          (int(self.x + shadow_offset), int(self.y + shadow_offset)), 
                          self.radius)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (200, 200, 200), (int(self.x), int(self.y)), self.radius, 2)

    def update(self):
        # Update position
        self.x += self.velocity[0]
        self.y += self.velocity[1]

        # Apply friction - more realistic
        self.velocity[0] *= self.friction
        self.velocity[1] *= self.friction

        # Stop very slow movement to prevent endless micro-movements
        if abs(self.velocity[0]) < self.min_velocity:
            self.velocity[0] = 0
        if abs(self.velocity[1]) < self.min_velocity:
            self.velocity[1] = 0

        # Boundary checks with smoother bouncing
        if self.x <= self.radius:
            self.x = self.radius
            self.velocity[0] = -self.velocity[0] * self.bounce_damping
        elif self.x >= 800 - self.radius:
            self.x = 800 - self.radius
            self.velocity[0] = -self.velocity[0] * self.bounce_damping

        if self.y <= self.radius:
            self.y = self.radius
            self.velocity[1] = -self.velocity[1] * self.bounce_damping
        elif self.y >= 600 - self.radius:
            self.y = 600 - self.radius
            self.velocity[1] = -self.velocity[1] * self.bounce_damping

    def possessed_by(self, players):
        """Check if any player is close enough to possess the ball"""
        closest_player = None
        min_distance = float('inf')

        for p in players:
            dist = math.hypot(self.x - p.x, self.y - p.y)
            if dist < min_distance:
                min_distance = dist
                closest_player = p

        # Possession range varies by role
        possession_range = 15
        if closest_player:
            if closest_player.role == "GK":
                possession_range = 20
            elif closest_player.role in ["CB", "LB", "RB"]:
                possession_range = 16

            if min_distance < possession_range:
                return closest_player

        return None

    def reset(self):
        """Reset ball to center of field"""
        self.x = 400
        self.y = 300
        self.velocity = [0, 0]
        self.last_passer = None

    def kick(self, direction_x, direction_y, power=1.0):
        """Apply a kick to the ball"""
        max_power = 8.0
        self.velocity[0] = direction_x * max_power * power
        self.velocity[1] = direction_y * max_power * power
