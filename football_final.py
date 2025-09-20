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
pygame.display.set_caption("Football Simulation - Version 0.2")
clock = pygame.time.Clock()

# Colors
GREEN = (34, 139, 34)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GREEN = (50, 205, 50)

def draw_field(screen):
    """Draw the football field with proper markings"""
    # Grass pattern
    for i in range(0, WIDTH, 40):
        color = GREEN if (i // 40) % 2 == 0 else LIGHT_GREEN
        pygame.draw.rect(screen, color, (i, 0, 40, HEIGHT))

    # Center line
    pygame.draw.line(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)

    # Center circle
    pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2), 80, 3)
    pygame.draw.circle(screen, WHITE, (WIDTH//2, HEIGHT//2), 3)

    # Goals
    pygame.draw.rect(screen, WHITE, (0, 250, 10, 100), 3)
    pygame.draw.rect(screen, WHITE, (790, 250, 10, 100), 3)

    # Penalty areas
    pygame.draw.rect(screen, WHITE, (0, 180, 80, 240), 3)
    pygame.draw.rect(screen, WHITE, (720, 180, 80, 240), 3)

    # Goal areas
    pygame.draw.rect(screen, WHITE, (0, 220, 40, 160), 3)
    pygame.draw.rect(screen, WHITE, (760, 220, 40, 160), 3)

    # Corner arcs
    pygame.draw.arc(screen, WHITE, (-10, -10, 20, 20), 0, math.pi/2, 3)
    pygame.draw.arc(screen, WHITE, (790, -10, 20, 20), math.pi/2, math.pi, 3)
    pygame.draw.arc(screen, WHITE, (-10, 590, 20, 20), 3*math.pi/2, 2*math.pi, 3)
    pygame.draw.arc(screen, WHITE, (790, 590, 20, 20), math.pi, 3*math.pi/2, 3)

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

print("=== FOOTBALL SIMULATION CONTROLS ===")
print("SPACE: Pause/Resume")
print("R: Reset Game")
print("Mouse Click: Kick Ball")
print("ESC: Quit Game")
print("====================================")

# Game loop
running = True
while running:
    dt = clock.tick(60)  # 60 FPS

    if not paused:
        game_time += dt

    draw_field(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                print("Game paused" if paused else "Game resumed")
            elif event.key == pygame.K_r:
                ball.reset()
                for player in players:
                    player.reset_position()
                score = {"A": 0, "B": 0}
                game_time = 0
                print("Game reset!")
            elif event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not paused:
            mx, my = pygame.mouse.get_pos()
            dx = mx - ball.x
            dy = my - ball.y
            mag = math.hypot(dx, dy)
            if mag != 0:
                # Normalize and apply kick
                power = min(1.0, mag / 100.0)  # Power based on distance
                ball.kick(dx / mag, dy / mag, power)

    if not paused:
        # Update ball
        ball.update()

        # Update all players
        for player in players:
            player.decide_action(ball, players, dt)
            player.update_movement(dt)
            player.update(dt)

        # Possession logic
        possessor = ball.possessed_by(players)

        if possessor:
            # Less frequent decision making for smoother gameplay
            if random.random() < 0.02:  # 2% chance per frame = ~1.2 times per second
                action = random.random()

                # SHOOT if close to goal
                if (possessor.team == "A" and ball.x > 650) or (possessor.team == "B" and ball.x < 150):
                    goal_x = 800 if possessor.team == "A" else 0
                    goal_y = 300 + random.uniform(-40, 40)
                    dx = goal_x - ball.x
                    dy = goal_y - ball.y
                    mag = math.hypot(dx, dy)
                    if mag > 0:
                        ball.kick(dx / mag, dy / mag, random.uniform(0.8, 1.0))
                    ball.last_passer = None

                # PASS
                elif action < 0.7:
                    teammates = [p for p in players if p.team == possessor.team and p != possessor]
                    teammates = [p for p in teammates if p != ball.last_passer]

                    visible = [p for p in teammates if possessor.can_see(p)]

                    if visible:
                        # Smart pass selection
                        if possessor.team == "A":
                            forward_players = [p for p in visible if p.x > possessor.x - 30]
                            candidates = forward_players if forward_players else visible
                        else:
                            forward_players = [p for p in visible if p.x < possessor.x + 30]
                            candidates = forward_players if forward_players else visible

                        if candidates:
                            target_player = random.choice(candidates)
                            dx = target_player.x - ball.x
                            dy = target_player.y - ball.y
                            mag = math.hypot(dx, dy)
                            if mag > 0:
                                pass_power = min(1.0, mag / 150.0)
                                ball.kick(dx / mag, dy / mag, pass_power)
                            ball.last_passer = possessor

                # DRIBBLE
                else:
                    direction = 1 if possessor.team == "A" else -1
                    dx = direction + random.uniform(-0.5, 0.5)
                    dy = random.uniform(-0.5, 0.5)
                    mag = math.hypot(dx, dy)
                    if mag > 0:
                        ball.kick(dx / mag, dy / mag, 0.4)

        # Tackling
        for opponent in players:
            if possessor and opponent.team != possessor.team:
                if opponent.attempt_tackle(possessor):
                    print(f"{opponent.role} tackles {possessor.role}!")
                    # Loose ball
                    dx = random.uniform(-1, 1)
                    dy = random.uniform(-1, 1)
                    mag = math.hypot(dx, dy)
                    if mag > 0:
                        ball.kick(dx / mag, dy / mag, 0.3)
                    ball.last_passer = None
                    break

        # Goal check
        if LEFT_GOAL.collidepoint(ball.x, ball.y):
            score["B"] += 1
            ball.reset()
            for player in players:
                player.reset_position()
            print(f"GOAL! Team B scores! Score: {score['A']} - {score['B']}")
        elif RIGHT_GOAL.collidepoint(ball.x, ball.y):
            score["A"] += 1
            ball.reset()
            for player in players:
                player.reset_position()
            print(f"GOAL! Team A scores! Score: {score['A']} - {score['B']}")

    # Draw all players
    for player in players:
        player.draw(screen)

    # Draw ball
    ball.draw(screen)

    # UI
    font = pygame.font.SysFont('Arial', 32, bold=True)
    score_text = font.render(f"{score['A']} - {score['B']}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH//2, 30))

    # Score background
    pygame.draw.rect(screen, (0, 0, 0, 128), score_rect.inflate(20, 10))
    screen.blit(score_text, score_rect)

    # Team labels
    small_font = pygame.font.SysFont('Arial', 18)
    team_a_text = small_font.render("Team A", True, BLUE)
    team_b_text = small_font.render("Team B", True, RED)
    screen.blit(team_a_text, (score_rect.left - 60, 25))
    screen.blit(team_b_text, (score_rect.right + 10, 25))

    # Game time
    minutes = int(game_time // 60000)
    seconds = int((game_time % 60000) // 1000)
    time_text = small_font.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
    screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, 55))

    # Pause indicator
    if paused:
        pause_font = pygame.font.SysFont('Arial', 48, bold=True)
        pause_text = pause_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        pygame.draw.rect(screen, (0, 0, 0, 180), pause_rect.inflate(40, 20))
        screen.blit(pause_text, pause_rect)

    pygame.display.flip()

print("Game ended. Final score:", score)
pygame.quit()
