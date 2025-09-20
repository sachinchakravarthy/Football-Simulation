import pygame
import math
import random
from player import Player
from ball import Ball
from formations import formation_433

# Setup
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Simulation - Improved")
clock = pygame.time.Clock()

# Colors
GREEN = (34, 139, 34)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def draw_field(screen):
    """Draw the football field with proper markings"""
    screen.fill(GREEN)

    # Center line
    pygame.draw.line(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)

    # Center circle
    pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2), 80, 3)

    # Goals
    pygame.draw.rect(screen, WHITE, (0, 250, 10, 100), 3)
    pygame.draw.rect(screen, WHITE, (790, 250, 10, 100), 3)

    # Penalty areas
    pygame.draw.rect(screen, WHITE, (0, 180, 80, 240), 3)
    pygame.draw.rect(screen, WHITE, (720, 180, 80, 240), 3)

# Create players
players = []

# Team A (left) - Blue
for i, (role, x, y) in enumerate(formation_433("left")):
    players.append(Player(x, y, team="A", name=f"A{i+1}", role=role, color=BLUE))

# Team B (right) - Red  
for i, (role, x, y) in enumerate(formation_433("right")):
    players.append(Player(x, y, team="B", name=f"B{i+1}", role=role, color=RED))

# Ball
ball = Ball(400, 300)

# Game state
score = {"A": 0, "B": 0}
LEFT_GOAL = pygame.Rect(0, 250, 10, 100)
RIGHT_GOAL = pygame.Rect(790, 250, 10, 100)
game_time = 0
paused = False

# Game loop
running = True
while running:
    dt = clock.tick(60)  # Delta time in milliseconds

    if not paused:
        game_time += dt

    draw_field(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key == pygame.K_r:
                # Reset game
                ball.reset()
                for player in players:
                    player.reset_position()
                score = {"A": 0, "B": 0}
                game_time = 0
        if event.type == pygame.MOUSEBUTTONDOWN and not paused:
            mx, my = pygame.mouse.get_pos()
            dx = mx - ball.x
            dy = my - ball.y
            mag = math.hypot(dx, dy)
            if mag != 0:
                ball.velocity = [4 * dx / mag, 4 * dy / mag]

    if not paused:
        # Update ball
        ball.update()

        # Update all players - THIS IS THE KEY CHANGE
        for player in players:
            player.decide_action(ball, players, dt)
            player.update_movement(dt)
            player.update(dt)

        # --- Enhanced Possession logic ---
        possessor = ball.possessed_by(players)

        if possessor:
            # Make decisions less frequently to avoid rapid changes
            action = random.random()

            # --- SHOOT if close to goal ---
            if (possessor.team == "A" and ball.x > 650) or (possessor.team == "B" and ball.x < 150):
                goal_x = 800 if possessor.team == "A" else 0
                goal_y = 300 + random.uniform(-30, 30)  # Add some variation
                target = (goal_x, goal_y)
                ball.last_passer = None

            # --- PASS ---
            elif action < 0.65:  # Slightly higher pass probability
                teammates = [p for p in players if p.team == possessor.team and p != possessor]
                teammates = [p for p in teammates if p != ball.last_passer]

                visible = [p for p in teammates if possessor.can_see(p)]

                if visible:
                    if possessor.team == "A":
                        # Prefer forward passes
                        forward_candidates = [p for p in visible if p.x > possessor.x - 20]
                        candidates = forward_candidates if forward_candidates else visible
                    else:
                        forward_candidates = [p for p in visible if p.x < possessor.x + 20]
                        candidates = forward_candidates if forward_candidates else visible

                    if candidates:
                        # Weight selection towards better positioned players
                        weights = []
                        for p in candidates:
                            # Prefer players closer to opponent goal
                            if possessor.team == "A":
                                goal_distance = abs(800 - p.x)
                            else:
                                goal_distance = abs(0 - p.x)
                            weight = 1.0 / (goal_distance + 50)  # +50 to avoid division by zero
                            weights.append(weight)

                        target_player = random.choices(candidates, weights=weights)[0]
                        # Add some lead to the pass
                        lead_x = 10 if possessor.team == "A" else -10
                        target = (target_player.x + lead_x, target_player.y)
                        ball.last_passer = possessor
                    else:
                        # Dribble if no good pass
                        dribble_distance = random.uniform(25, 45)
                        target = (possessor.x + (dribble_distance if possessor.team == "A" else -dribble_distance), 
                                possessor.y + random.uniform(-20, 20))
                        ball.last_passer = None
                else:
                    # Nobody visible → dribble forward
                    dribble_distance = random.uniform(20, 40)
                    target = (possessor.x + (dribble_distance if possessor.team == "A" else -dribble_distance), 
                            possessor.y + random.uniform(-15, 15))
                    ball.last_passer = None

            # --- DRIBBLE ---
            else:
                dribble_distance = random.uniform(30, 50)
                target = (possessor.x + (dribble_distance if possessor.team == "A" else -dribble_distance), 
                        possessor.y + random.uniform(-25, 25))
                ball.last_passer = None

            # --- Enhanced Tackling ---
            tackle_attempts = []
            for p in players:
                if p.team != possessor.team:
                    distance = math.hypot(p.x - possessor.x, p.y - possessor.y)
                    if distance < 40:  # Only nearby opponents attempt tackles
                        tackle_attempts.append((p, distance))

            # Sort by distance and let closest opponent attempt tackle
            if tackle_attempts:
                tackle_attempts.sort(key=lambda x: x[1])
                closest_opponent = tackle_attempts[0][0]

                if closest_opponent.attempt_tackle(possessor):
                    print(f"{closest_opponent.role} from Team {closest_opponent.team} tackled {possessor.role}!")
                    possessor = closest_opponent
                    target = (possessor.x + random.uniform(-10, 10), 
                            possessor.y + random.uniform(-10, 10))
                    ball.last_passer = None

            # --- Move ball toward target with some variation ---
            dx = target[0] - ball.x
            dy = target[1] - ball.y
            mag = math.hypot(dx, dy)
            if mag != 0:
                speed = random.uniform(4.0, 6.0)  # Variable ball speed
                ball.velocity = [speed * dx / mag, speed * dy / mag]

        # --- Goal check ---
        if LEFT_GOAL.collidepoint(ball.x, ball.y):
            score["B"] += 1
            ball.reset()
            for player in players:
                player.reset_position()
            print(f"GOAL! Team B scores! {score['A']} - {score['B']}")
        elif RIGHT_GOAL.collidepoint(ball.x, ball.y):
            score["A"] += 1
            ball.reset()
            for player in players:
                player.reset_position()
            print(f"GOAL! Team A scores! {score['A']} - {score['B']}")

    # Draw all players
    for player in players:
        player.draw(screen)

    # Draw ball
    ball.draw(screen)

    # Draw UI
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Team A: {score['A']} - {score['B']} :Team B", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 20))

    # Game time
    minutes = int(game_time // 60000)
    seconds = int((game_time % 60000) // 1000)
    time_text = font.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
    screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 60))

    # Instructions
    if paused:
        pause_text = font.render("PAUSED - Press SPACE to resume", True, WHITE)
        screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2))

    small_font = pygame.font.SysFont(None, 20)
    instructions = [
        "SPACE: Pause/Resume",
        "R: Reset Game", 
        "Click: Kick Ball",
        "Yellow dots: Ball chasers",
        "Green dots: Supporting players"
    ]
    for i, instruction in enumerate(instructions):
        text = small_font.render(instruction, True, WHITE)
        screen.blit(text, (10, HEIGHT - 120 + i * 22))

    pygame.display.flip()

pygame.quit()
