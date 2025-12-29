import pygame
import random
import math
import os

pygame.init()
pygame.mixer.init()

# ---------- ЭКРАН ----------
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
pygame.display.set_caption("Hybrid Shooter")
clock = pygame.time.Clock()

# ---------- ЦВЕТА ----------
WHITE = (255, 255, 255)
RED = (220, 50, 50)
BLACK = (0, 0, 0)

# ---------- ШРИФТЫ ----------
FONT = pygame.font.SysFont(None, 36)
BIG_FONT = pygame.font.SysFont(None, 56)

# ---------- СОСТОЯНИЯ ----------
MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"
state = MENU

# ---------- BEST SCORE ----------
BEST_SCORE_FILE = "best_score.txt"

def load_best_score():
    if os.path.exists(BEST_SCORE_FILE):
        try:
            return int(open(BEST_SCORE_FILE).read())
        except:
            return 0
    return 0

def save_best_score(s):
    open(BEST_SCORE_FILE, "w").write(str(s))

best_score = load_best_score()

# ---------- ЗВУКИ ----------
shoot_snd = pygame.mixer.Sound("sounds/shoot.wav")
hit_snd = pygame.mixer.Sound("sounds/hit.wav")
hurt_snd = pygame.mixer.Sound("sounds/hurt.wav")
game_over_snd = pygame.mixer.Sound("sounds/game_over.wav")

# ---------- ЛОКАЦИЯ ----------
MAP_W, MAP_H = 3000, 3000
map_img = pygame.image.load("map.png").convert()
map_img = pygame.transform.scale(map_img, (MAP_W, MAP_H))

# ---------- ИГРОК ----------
player_pos = pygame.Vector2(MAP_W // 2, MAP_H // 2)
player_speed = 5
player_speed_normal = 5
player_speed_sprint = 9
player_hp = 5

player_angle = 0
target_angle = 0
ROTATE_SMOOTH = 0.15

player_img = pygame.image.load("player.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (48, 48))
PLAYER_RADIUS = 20

# ---------- ТОЧКА ДУЛА ----------
GUN_POINT_LOCAL = pygame.Vector2(42, 24)

# ---------- СТРЕЛЬБА ----------
bullets = []
bullet_speed = 50
shoot_cooldown = 200
last_shot_time = 0

# ---------- УЛЬТА ----------
ult_bullets = []
ULT_COOLDOWN = 30000
ULT_SPEED = 4
ULT_RADIUS = 220
ULT_LIFETIME = 1500
last_ult_time = -ULT_COOLDOWN

# ---------- ТАНК-ЗОМБИ ----------
tank_enemies = []
TANK_HP = 5
TANK_SPAWN_COOLDOWN = 30000
last_tank_spawn = 0

# ---------- ОБЫЧНЫЕ ВРАГИ ----------
enemies = []
enemy_img = pygame.image.load("enemy.png").convert_alpha()
enemy_img = pygame.transform.scale(enemy_img, (48, 48))

tank_img = pygame.image.load("tank_enemy.png").convert_alpha()
tank_img = pygame.transform.scale(tank_img, (64, 64)) # танк больше

def spawn_enemy():
    enemies.append(
        pygame.Vector2(
            random.randint(100, MAP_W - 100),
            random.randint(100, MAP_H - 100)
        )
    )

# ---------- СЧЁТ ----------
score = 0

def reset_game():
    global state, score, bullets, enemies, ult_bullets, tank_enemies
    global player_hp, player_angle, target_angle, player_pos

    score = 0
    bullets.clear()
    enemies.clear()
    ult_bullets.clear()
    tank_enemies.clear()

    player_hp = 5
    player_pos = pygame.Vector2(MAP_W // 2, MAP_H // 2)
    player_angle = 0
    target_angle = 0

    for _ in range(10):
        spawn_enemy()

    state = PLAYING

# ---------- ИГРА ----------
running = True
while running:
    clock.tick(60)
    now = pygame.time.get_ticks()
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()
    mouse = pygame.mouse.get_pressed()

    # ===== МЕНЮ =====
    if state == MENU:
        screen.blit(BIG_FONT.render("HYBRID SHOOTER", True, WHITE), (W//2-200, H//2-120))
        screen.blit(FONT.render("Press SPACE", True, WHITE), (W//2-90, H//2))
        screen.blit(FONT.render(f"Best: {best_score}", True, WHITE), (W//2-70, H//2+40))

        if keys[pygame.K_SPACE]:
            reset_game()

        pygame.display.flip()
        continue

    # ===== GAME OVER =====
    if state == GAME_OVER:
        screen.blit(BIG_FONT.render("GAME OVER", True, RED), (W//2-160, H//2-80))
        screen.blit(FONT.render(f"Score: {score}", True, WHITE), (W//2-70, H//2))
        screen.blit(FONT.render("Press R", True, WHITE), (W//2-40, H//2+40))

        if keys[pygame.K_r]:
            reset_game()

        pygame.display.flip()
        continue

    # ===== GAMEPLAY =====

    # ===== КАМЕРА =====
    cam_x = max(0, min(player_pos.x - W//2, MAP_W - W))
    cam_y = max(0, min(player_pos.y - H//2, MAP_H - H))

    screen.blit(map_img, (-cam_x, -cam_y))

    # ===== ДВИЖЕНИЕ =====
    move = pygame.Vector2(0, 0)
    if keys[pygame.K_w]: move.y -= 1
    if keys[pygame.K_s]: move.y += 1
    if keys[pygame.K_a]: move.x -= 1
    if keys[pygame.K_d]: move.x += 1

    # спринт (Shift)
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        player_speed = player_speed_sprint
    else:
        player_speed = player_speed_normal

    if move.length_squared() > 0:
        move = move.normalize()
        player_pos += move * player_speed
        if not mouse[0]:
            target_angle = -math.degrees(math.atan2(move.y, move.x))

    # ===== ОГРАНИЧЕНИЯ =====
    player_pos.x = max(PLAYER_RADIUS, min(player_pos.x, MAP_W - PLAYER_RADIUS))
    player_pos.y = max(PLAYER_RADIUS, min(player_pos.y, MAP_H - PLAYER_RADIUS))

    # ===== СПАВН ТАНКА =====
    if now - last_tank_spawn >= TANK_SPAWN_COOLDOWN:
        tank_enemies.append({
            "pos": pygame.Vector2(
                random.randint(150, MAP_W - 150),
                random.randint(150, MAP_H - 150)
            ),
            "hp": TANK_HP
        })
        last_tank_spawn = now

    # ===== СТРЕЛЬБА =====
    mouse_pos = pygame.Vector2(pygame.mouse.get_pos()) + pygame.Vector2(cam_x, cam_y)
    aim = mouse_pos - player_pos

    if mouse[0] and now - last_shot_time >= shoot_cooldown and aim.length_squared() > 0:
        direction = aim.normalize()

        # вращение дула
        offset = GUN_POINT_LOCAL - pygame.Vector2(24, 24)
        rad = math.radians(player_angle)

        rotated = pygame.Vector2(
            offset.x * math.cos(rad) - offset.y * math.sin(rad),
            offset.x * math.sin(rad) + offset.y * math.cos(rad)
        )

        bullet_pos = player_pos + rotated
        bullets.append([bullet_pos, direction])

        shoot_snd.play()
        last_shot_time = now
        target_angle = -math.degrees(math.atan2(direction.y, direction.x))

    # ===== УЛЬТА =====
    if keys[pygame.K_e] and now - last_ult_time >= ULT_COOLDOWN and aim.length_squared() > 0:
        ult_bullets.append({
            "pos": player_pos.copy(),
            "dir": aim.normalize(),
            "spawn": now
        })
        last_ult_time = now

    # ===== ПОВОРОТ ИГРОКА =====
    diff = (target_angle - player_angle + 180) % 360 - 180
    player_angle += diff * ROTATE_SMOOTH

    rot_player = pygame.transform.rotate(player_img, player_angle)
    screen.blit(rot_player, rot_player.get_rect(center=(player_pos.x - cam_x, player_pos.y - cam_y)))

    # ===== ПУЛИ =====
    for b in bullets[:]:
        b[0] += b[1] * bullet_speed

        px = int(b[0].x - cam_x)
        py = int(b[0].y - cam_y)

        glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (0,180,255,120), (10,10), 9)
        pygame.draw.circle(glow, (0,255,255,200), (10,10), 5)
        screen.blit(glow, (px-10, py-10))

        if not (0 <= b[0].x <= MAP_W and 0 <= b[0].y <= MAP_H):
            bullets.remove(b)

    # ===== УЛЬТА (взрыв через 1.5 сек) =====
    for u in ult_bullets[:]:
        u["pos"] += u["dir"] * ULT_SPEED
        ux, uy = int(u["pos"].x - cam_x), int(u["pos"].y - cam_y)

        pygame.draw.circle(screen, (100,200,255), (ux,uy), 22)

        # взрыв
        if now - u["spawn"] >= ULT_LIFETIME:
            pygame.draw.circle(screen, (80,180,255), (ux, uy), ULT_RADIUS)

            for e in enemies[:]:
                if e.distance_to(u["pos"]) < ULT_RADIUS:
                    enemies.remove(e)
                    score += 1
                    spawn_enemy()

            for t in tank_enemies[:]:
                if t["pos"].distance_to(u["pos"]) < ULT_RADIUS:
                    t["hp"] -= 5
                    if t["hp"] <= 0:
                        tank_enemies.remove(t)
                        score += 3

            ult_bullets.remove(u)
            continue

        # исчезает за картой
        if not (0 <= u["pos"].x <= MAP_W and 0 <= u["pos"].y <= MAP_H):
            ult_bullets.remove(u)

    # ===== ОБЫЧНЫЕ ЗОМБИ =====
    for e in enemies[:]:
        d = player_pos - e
        if d.length_squared() > 0:
            e += d.normalize() * 2
            ang = -math.degrees(math.atan2(d.y, d.x))
        else:
            ang = 0

        rot_e = pygame.transform.rotate(enemy_img, ang)
        screen.blit(rot_e, rot_e.get_rect(center=(e.x - cam_x, e.y - cam_y)))

        if e.distance_to(player_pos) < 20:
            enemies.remove(e)
            player_hp -= 1
            hurt_snd.play()
            spawn_enemy()
            continue

        for b in bullets[:]:
            if e.distance_to(b[0]) < 24:
                enemies.remove(e)
                bullets.remove(b)
                score += 1
                hit_snd.play()
                spawn_enemy()
                break

    # ===== ТАНК-ЗОМБИ =====
    for t in tank_enemies[:]:
        d = player_pos - t["pos"]

        if d.length_squared() > 0:
            t["pos"] += d.normalize() * 1.2
            ang = -math.degrees(math.atan2(d.y, d.x))
        else:
            ang = 0

        rot_t = pygame.transform.rotate(tank_img, ang)
        screen.blit(rot_t, rot_t.get_rect(center=(t["pos"].x - cam_x, t["pos"].y - cam_y)))

        if t["pos"].distance_to(player_pos) < 25:
            t["hp"] -= 1
            if t["hp"] <= 0:
                tank_enemies.remove(t)
                score += 3
            player_hp -= 1
            hurt_snd.play()
            continue

        for b in bullets[:]:
            if t["pos"].distance_to(b[0]) < 20:
                t["hp"] -= 1
                bullets.remove(b)
                if t["hp"] <= 0:
                    tank_enemies.remove(t)
                    score += 3
                break

    # ===== UI =====
    screen.blit(FONT.render(f"HP: {player_hp}", True, WHITE), (10,10))
    screen.blit(FONT.render(f"Score: {score}", True, WHITE), (10,40))

    # индикатор ульты
    cd = max(0, (ULT_COOLDOWN - (now - last_ult_time)) // 1000)
    if cd == 0:
        txt = FONT.render("ULT: READY (E)", True, (0,255,255))
    else:
        txt = FONT.render(f"ULT CD: {cd}s", True, (150,150,150))
    screen.blit(txt, (10,70))

    # смерть
    if player_hp <= 0:
        if score > best_score:
            save_best_score(score)
        game_over_snd.play()
        state = GAME_OVER

    pygame.display.flip()

pygame.quit()