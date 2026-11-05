"""Arena Duel – original one-on-one first-person arena shooter vs. a bot.

Controls: WASD move, mouse aim, left click fire, R reload, Shift sprint,
ESC pause/release mouse, Tab toggle minimap, Enter start/restart.

Requires pygame >= 2.5.0. Run with: python arena_duel.py
"""
import math
import random
import sys
import pygame

from game_math import LEVEL, cast_ray, line_of_sight, move_colliding, nav_direction

W, H = 1024, 640
HALF_W, HALF_H = W // 2, H // 2
FOV = math.radians(70)
PLANE = math.tan(FOV / 2)
BG = (10, 15, 26)
WHITE = (235, 247, 255)
CYAN = (66, 223, 251)
ORANGE = (255, 137, 91)

DIFFICULTIES = ("EINFACH", "NORMAL", "SCHWER")


def clamp(value, a, b):
    return max(a, min(b, value))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ARENA DUEL  |  1v1 BOT")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("segoeui", 64, bold=True)
        self.font_med = pygame.font.SysFont("segoeui", 29, bold=True)
        self.font_small = pygame.font.SysFont("segoeui", 19, bold=True)
        self.font_micro = pygame.font.SysFont("segoeui", 15)
        self.difficulty = 1
        self.state = "menu"
        self.show_minimap = True
        self.elapsed = 0
        self.running = True
        self.reset_match()
        pygame.mouse.set_visible(True)

    def reset_match(self):
        self.player_x, self.player_y = 3.5, 6.5
        self.player_angle = 0.0
        self.player_hp = 100
        self.player_respawn = 0.0
        self.bot_x, self.bot_y = 16.5, 6.5
        self.bot_hp = 100
        self.bot_respawn = 0.0
        self.bot_cooldown = 1.8
        self.bot_strafe_dir = -1
        self.bot_strafe_timer = 0.6
        self.ammo = 16
        self.max_ammo = 16
        self.reload_timer = 0.0
        self.fire_timer = 0.0
        self.hit_flash = 0.0
        self.damage_flash = 0.0
        self.muzzle_flash = 0.0
        self.banner_text = ""
        self.banner_timer = 0.0
        self.player_score = 0
        self.bot_score = 0
        self.match_time = 120.0
        self.elapsed = 0.0
        self.winner = None

    def capture_mouse(self, capture):
        pygame.event.set_grab(capture)
        pygame.mouse.set_visible(not capture)
        pygame.mouse.get_rel()

    def start(self):
        self.reset_match()
        self.state = "playing"
        self.capture_mouse(True)

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.capture_mouse(False)
        elif self.state == "paused":
            self.state = "playing"
            self.capture_mouse(True)

    def banner(self, message, seconds=1.15):
        self.banner_text = message
        self.banner_timer = seconds

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state in ("menu", "over"):
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.start()
                    elif self.state == "menu" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        self.difficulty = event.key - pygame.K_1
                elif event.key == pygame.K_ESCAPE:
                    self.toggle_pause()
                elif self.state == "paused":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.toggle_pause()
                    elif event.key == pygame.K_m:
                        self.state = "menu"
                elif self.state == "playing":
                    if event.key == pygame.K_r:
                        self.reload()
                    elif event.key == pygame.K_TAB:
                        self.show_minimap = not self.show_minimap
            elif event.type == pygame.MOUSEMOTION and self.state == "playing":
                self.player_angle = (self.player_angle + event.rel[0] * .0027) % (2 * math.pi)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "playing" and event.button == 1:
                    self.fire()
                elif self.state in ("menu", "over") and event.button == 1:
                    self.start()

    def reload(self):
        if self.reload_timer <= 0 and self.ammo < self.max_ammo and self.player_hp > 0:
            self.reload_timer = 1.15
            self.banner("NACHLADEN ...", .7)

    def bot_screen(self):
        dx, dy = self.bot_x - self.player_x, self.bot_y - self.player_y
        fwd_x, fwd_y = math.cos(self.player_angle), math.sin(self.player_angle)
        side_x, side_y = -fwd_y, fwd_x
        depth = dx * fwd_x + dy * fwd_y
        lateral = dx * side_x + dy * side_y
        if depth <= .2:
            return None
        scale = HALF_W / PLANE
        screen_x = HALF_W + (lateral / depth) * scale
        height = min(1100, H / (depth * .78))
        width = height * .43
        return screen_x, depth, width, height

    def fire(self):
        if self.player_hp <= 0 or self.reload_timer > 0 or self.fire_timer > 0:
            return
        if self.ammo <= 0:
            self.reload()
            return
        self.ammo -= 1
        self.fire_timer = .17
        self.muzzle_flash = .11
        if self.bot_hp <= 0:
            return
        proj = self.bot_screen()
        if proj is None:
            return
        sx, depth, width, _ = proj
        if abs(sx - HALF_W) < max(6.5, width * .39) and line_of_sight(
            LEVEL, self.player_x, self.player_y, self.bot_x, self.bot_y
        ):
            self.bot_hp = max(0, self.bot_hp - 26)
            self.hit_flash = .18
            if self.bot_hp == 0:
                self.player_score += 1
                self.banner("BOT ELIMINIERT  +1", 1.8)
                self.bot_respawn = 1.6
                if self.player_score >= 5:
                    self.finish()
            else:
                self.banner("TREFFER!", .38)

    def finish(self):
        self.state = "over"
        self.capture_mouse(False)
        if self.player_score > self.bot_score:
            self.winner = "GEWONNEN"
        elif self.player_score < self.bot_score:
            self.winner = "VERLOREN"
        else:
            self.winner = "UNENTSCHIEDEN"

    def bot_update(self, dt):
        if self.bot_hp <= 0:
            self.bot_respawn -= dt
            if self.bot_respawn <= 0 and self.state == "playing":
                self.bot_x, self.bot_y = (16.5, 6.5) if self.player_x < 9 else (3.5, 6.5)
                self.bot_hp = 100
                self.bot_cooldown = 1.0
            return
        if self.player_hp <= 0:
            return
        dx, dy = self.player_x - self.bot_x, self.player_y - self.bot_y
        dist = math.hypot(dx, dy) or 1
        visible = line_of_sight(LEVEL, self.bot_x, self.bot_y, self.player_x, self.player_y)
        self.bot_strafe_timer -= dt
        if self.bot_strafe_timer <= 0:
            self.bot_strafe_timer = random.uniform(.9, 2.0)
            self.bot_strafe_dir *= -1
        if visible:
            forward = 1.0 if dist > 6.0 else (-.75 if dist < 3.4 else .02)
            strafe = .83 * self.bot_strafe_dir
            vx = (dx / dist) * forward + (-dy / dist) * strafe
            vy = (dy / dist) * forward + (dx / dist) * strafe
        else:
            vx, vy = nav_direction(LEVEL, self.bot_x, self.bot_y, self.player_x, self.player_y)
        mag = math.hypot(vx, vy) or 1
        speed = (2.0, 2.45, 2.8)[self.difficulty]
        old_x, old_y = self.bot_x, self.bot_y
        self.bot_x, self.bot_y = move_colliding(
            LEVEL, self.bot_x, self.bot_y, vx / mag * speed * dt, vy / mag * speed * dt, .25)
        if math.hypot(self.bot_x - old_x, self.bot_y - old_y) < .003 and visible:
            self.bot_strafe_dir *= -1
        self.bot_cooldown -= dt
        if visible and dist < 19 and self.bot_cooldown <= 0:
            self.bot_cooldown = random.uniform(*( ((1.3, 1.8), (0.92, 1.32), (.69, 1.08))[self.difficulty]))
            if random.random() < (.48, .68, .80)[self.difficulty]:
                self.player_hp = max(0, self.player_hp - (10, 13, 16)[self.difficulty])
                self.damage_flash = .26
                if self.player_hp == 0:
                    self.bot_score += 1
                    self.banner("DU WURDEST ELIMINIERT", 1.5)
                    self.player_respawn = 1.65
                    if self.bot_score >= 5:
                        self.finish()

    def update(self, dt):
        if self.state != "playing":
            return
        self.match_time = max(0, self.match_time - dt)
        self.elapsed += dt
        if self.match_time <= 0:
            self.finish()
            return
        self.fire_timer = max(0, self.fire_timer - dt)
        self.muzzle_flash = max(0, self.muzzle_flash - dt)
        self.hit_flash = max(0, self.hit_flash - dt)
        self.damage_flash = max(0, self.damage_flash - dt)
        self.banner_timer = max(0, self.banner_timer - dt)
        if self.reload_timer > 0:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.ammo = self.max_ammo
                self.reload_timer = 0
        if self.player_hp <= 0:
            self.player_respawn -= dt
            if self.player_respawn <= 0:
                self.player_hp = 100
                self.player_x, self.player_y = (3.5, 6.5) if self.bot_x > 10 else (16.5, 6.5)
                self.ammo = self.max_ammo
                self.reload_timer = 0
                self.bot_cooldown = max(self.bot_cooldown, 1.1)
        else:
            keys = pygame.key.get_pressed()
            f_x, f_y = math.cos(self.player_angle), math.sin(self.player_angle)
            r_x, r_y = -f_y, f_x
            fw = int(keys[pygame.K_w]) - int(keys[pygame.K_s])
            strafe = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
            vx, vy = f_x * fw + r_x * strafe, f_y * fw + r_y * strafe
            mag = math.hypot(vx, vy)
            if mag:
                speed = 4.5 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 3.2
                self.player_x, self.player_y = move_colliding(
                    LEVEL, self.player_x, self.player_y, vx / mag * speed * dt, vy / mag * speed * dt)
        self.bot_update(dt)

    def text(self, text, x, y, font=None, color=WHITE, center=False):
        surf = (font or self.font_small).render(text, True, color)
        pos = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
        self.screen.blit(surf, pos)

    def render_arena(self):
        screen = self.screen
        # Cheap gradients keep the 3D world readable without external assets.
        for y in range(0, HALF_H, 3):
            t = y / HALF_H
            pygame.draw.rect(screen, (int(10 + 13*t), int(20 + 22*t), int(36 + 37*t)), (0, y, W, 3))
        for y in range(HALF_H, H, 3):
            t = (y - HALF_H) / HALF_H
            pygame.draw.rect(screen, (int(23 - 11*t), int(30 - 17*t), int(41 - 21*t)), (0, y, W, 3))
        fx, fy = math.cos(self.player_angle), math.sin(self.player_angle)
        plane_x, plane_y = -fy * PLANE, fx * PLANE
        zbuffer = []
        step = 4
        for x in range(0, W, step):
            camera_x = 2 * (x + step/2) / W - 1
            rx, ry = fx + plane_x * camera_x, fy + plane_y * camera_x
            distance, side, texture_x = cast_ray(LEVEL, self.player_x, self.player_y, rx, ry)
            zbuffer.append(distance)
            wall_h = min(1250, int(H / (distance * .80)))
            top = HALF_H - wall_h // 2
            light = clamp(1.18 - distance * .047, .36, 1)
            material = .74 if side else 1.0
            edge = .75 if texture_x < .035 or texture_x > .965 else 1.0
            color = (int(40 * light * material * edge),
                     int(103 * light * material * edge),
                     int(145 * light * material * edge))
            pygame.draw.rect(screen, color, (x, top, step + 1, wall_h))
            if wall_h > 10 and texture_x < .04:
                pygame.draw.line(screen, (30, 110, 155), (x, top), (x, top + wall_h), 1)
            if wall_h > 6:
                pygame.draw.line(screen, (69, 203, 238), (x, top), (x + step, top), 1)
        if self.bot_hp > 0:
            self.render_bot(zbuffer, step)
        # A handful of floor guide lines increase depth perception.
        for y in (H//2 + 85, H//2 + 162, H//2 + 240):
            pygame.draw.line(screen, (23, 46, 62), (0, y), (W, y), 1)
        self.render_weapon()

    def render_bot(self, zbuffer, step):
        proj = self.bot_screen()
        if not proj:
            return
        sx, depth, width, height = proj
        if sx < -width or sx > W + width:
            return
        col = int(clamp(sx // step, 0, len(zbuffer)-1))
        if depth > zbuffer[col] + .2:
            return
        if depth < .35:
            return
        cx = int(sx)
        h = int(clamp(height, 16, 740))
        bw = int(clamp(width, 8, 290))
        bottom = HALF_H + int(h*.48)
        top = bottom - h
        body = pygame.Rect(cx - bw // 2, top + int(h * .30), bw, int(h*.48))
        head = pygame.Rect(cx - int(bw * .30), top + int(h * .05), int(bw*.60), int(h*.28))
        pygame.draw.ellipse(self.screen, (8, 12, 19), (cx-bw*.65, bottom-8, bw*1.3, 14))
        pygame.draw.rect(self.screen, (130, 51, 59), body, border_radius=max(2, int(h * .035)))
        pygame.draw.rect(self.screen, (222, 99, 89), body.inflate(-max(2,int(bw*.25)), -max(2,int(h*.16))),
                         border_radius=max(2, int(h*.02)))
        pygame.draw.rect(self.screen, (193, 80, 70), head, border_radius=max(2, int(h*.045)))
        visor = head.inflate(-max(2,int(bw*.19)), -max(2,int(h*.13)))
        pygame.draw.rect(self.screen, CYAN, visor, border_radius=max(1, int(h*.02)))
        leg_w = max(2, int(bw * .31))
        for offset in (-.28, .18):
            leg = pygame.Rect(int(cx + bw*offset), top + int(h*.70), leg_w, int(h*.30))
            pygame.draw.rect(self.screen, (98, 47, 65), leg, border_radius=3)
        # Robot's weapon
        pygame.draw.line(self.screen, (41, 45, 66), (cx, top+int(h*.59)),
                         (cx+int(bw*.70), top+int(h*.65)), max(3,int(h*.075)))
        if h > 32:
            bar_w = int(max(32, bw*1.3))
            pygame.draw.rect(self.screen, (16, 20, 30), (cx-bar_w//2, top-17, bar_w, 7))
            pygame.draw.rect(self.screen, (ORANGE if self.bot_hp < 45 else CYAN),
                             (cx-bar_w//2, top-17, int(bar_w*self.bot_hp/100), 7))

    def render_weapon(self):
        g = self.screen
        # Stylized on-screen blaster at bottom center.
        pygame.draw.polygon(g, (25, 29, 47), [(W*.43,H), (W*.457,H*.83), (W*.54,H*.83), (W*.575,H)])
        pygame.draw.polygon(g, (65, 78, 101), [(W*.475,H), (W*.49,H*.77), (W*.52,H*.77), (W*.536,H)])
        pygame.draw.polygon(g, (44, 157, 185), [(W*.492,H*.82), (W*.498,H*.73), (W*.513,H*.73), (W*.520,H*.82)])
        pygame.draw.rect(g, (16, 23, 34), (int(W*.493), int(H*.705), int(W*.022), int(H*.07)), border_radius=3)
        if self.muzzle_flash > 0:
            points = [(HALF_W, H*.69), (HALF_W-28,H*.62), (HALF_W-12,H*.65),
                      (HALF_W,H*.55), (HALF_W+13,H*.65), (HALF_W+29,H*.62)]
            pygame.draw.polygon(g, (255, 195, 103), points)

    def render_hud(self):
        s = self.screen
        pygame.draw.rect(s, (11, 18, 29), (W//2-132, 9, 264, 67), border_radius=10)
        self.text(f"{self.player_score}  :  {self.bot_score}", HALF_W, 23,
                  self.font_med, WHITE, True)
        mins, secs = divmod(int(self.match_time), 60)
        self.text(f"ERSTER BIS 5  •  {mins:02d}:{secs:02d}", HALF_W, 57,
                  self.font_micro, (143, 178, 201), True)
        self.text("ARENA DUEL", 22, 15, self.font_med, CYAN)
        self.text(f"BOT: {DIFFICULTIES[self.difficulty]}", 24, 48,
                  self.font_micro, (158, 177, 200))
        pygame.draw.rect(s, (10, 16, 27), (17, H-87, 262, 66), border_radius=10)
        self.text(f"LEBEN  {self.player_hp}", 30, H-77, self.font_small, WHITE)
        pygame.draw.rect(s, (49, 50, 61), (30, H-46, 225, 13), border_radius=4)
        pygame.draw.rect(s, (255, 91, 91) if self.player_hp < 35 else (72, 227, 164),
                         (30, H-46, int(225*self.player_hp/100), 13), border_radius=4)
        pygame.draw.rect(s, (10, 16, 27), (W-230, H-88, 210, 67), border_radius=10)
        self.text("BLASTER", W-212, H-80, self.font_micro, (147,175,196))
        self.text(f"{self.ammo:02d} / {self.max_ammo:02d}", W-205, H-60, self.font_med)
        if self.reload_timer > 0:
            self.text("NACHLADEN", W-121, H-54, self.font_micro, ORANGE)
        center = (HALF_W, HALF_H)
        color = ORANGE if self.hit_flash > 0 else CYAN
        size = 11 if self.hit_flash else 9
        for dx, dy, ex, ey in [(-size-7,0,-size,0),(size,0,size+7,0),(0,-size-7,0,-size),(0,size,0,size+7)]:
            pygame.draw.line(s, color, (center[0]+dx, center[1]+dy),
                             (center[0]+ex,center[1]+ey), 2)
        pygame.draw.circle(s, WHITE, center, 2)
        if self.banner_timer > 0:
            self.text(self.banner_text, HALF_W, 112, self.font_med,
                      ORANGE if "ELIMINIERT" in self.banner_text else CYAN, True)
        if self.damage_flash > 0:
            overlay = pygame.Surface((W,H),pygame.SRCALPHA)
            strength = int(70 * self.damage_flash/.26)
            overlay.fill((255, 42, 42, strength))
            s.blit(overlay, (0,0))
        if self.player_hp == 0:
            self.text("RESPAWN ...", HALF_W, HALF_H - 80, self.font_big, ORANGE, True)
        self.text("WASD: Bewegen   |   MAUS: Zielen/Schießen   |   R: Nachladen   |   ESC: Pause",
                  HALF_W, H-12, self.font_micro, (130, 155, 173), True)
        if self.show_minimap:
            self.render_map()

    def render_map(self):
        tile = 8
        left, top = W-190, 21
        w = len(LEVEL[0]) * tile
        h = len(LEVEL) * tile
        pygame.draw.rect(self.screen, (10, 18, 31), (left-8, top-8, w+16, h+16), border_radius=8)
        for gy, row in enumerate(LEVEL):
            for gx, cell in enumerate(row):
                if cell == '#':
                    pygame.draw.rect(self.screen, (52, 96, 120), (left+gx*tile, top+gy*tile, tile-1,tile-1))
        px = int(left+self.player_x*tile)
        py = int(top+self.player_y*tile)
        pygame.draw.circle(self.screen, CYAN, (px,py),4)
        pygame.draw.line(self.screen, CYAN, (px,py),
                         (int(px+math.cos(self.player_angle)*12),int(py+math.sin(self.player_angle)*12)), 2)
        if self.bot_hp > 0:
            pygame.draw.circle(self.screen, ORANGE,
                               (int(left+self.bot_x*tile), int(top+self.bot_y*tile)), 4)
        self.text("TAB: MAP", left, top+h+2, self.font_micro, (128, 164, 189))

    def overlay(self, title, subtitle, lines):
        cover = pygame.Surface((W,H),pygame.SRCALPHA)
        cover.fill((4,9,18,211))
        self.screen.blit(cover,(0,0))
        self.text(title, HALF_W, 162, self.font_big, CYAN, True)
        self.text(subtitle, HALF_W, 239, self.font_med, WHITE, True)
        for i, ln in enumerate(lines):
            self.text(ln, HALF_W, 301+i*36, self.font_small, (172,194,210), True)
        pygame.draw.rect(self.screen, (27, 117, 139), (HALF_W-197, 497, 394, 53), border_radius=9)
        self.text("ENTER  /  KLICK  —  START", HALF_W, 523, self.font_med, WHITE, True)

    def draw(self):
        if self.state == "menu":
            self.render_arena()
            self.overlay("ARENA DUEL", "1 GEGEN 1 BOT  •  EGO-SHOOTER",
                         ["Originales Arena-Spiel – kein offizielles Roblox-Spiel",
                          "Ziele mit der Maus, schieße mit linker Maustaste.",
                          "WASD bewegen  •  R nachladen  •  ESC Pause",
                          f"Schwierigkeit: {DIFFICULTIES[self.difficulty]}  (Tasten 1 / 2 / 3)"])
        elif self.state == "over":
            self.render_arena()
            self.overlay(self.winner or "SPIELENDE", f"ENDSTAND  {self.player_score} : {self.bot_score}",
                         ["Erster bis 5 Kills oder 2 Minuten Spielzeit.",
                          "Noch eine Runde? Starte das Duell erneut!"])
        else:
            self.render_arena()
            self.render_hud()
            if self.state == "paused":
                shade = pygame.Surface((W,H),pygame.SRCALPHA)
                shade.fill((0,0,0,165))
                self.screen.blit(shade,(0,0))
                self.text("PAUSE", HALF_W, 215, self.font_big, CYAN, True)
                self.text("ESC / ENTER: Weiter    |    M: Hauptmenü", HALF_W, 300,
                          self.font_small, WHITE, True)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000., .05)
            self.handle_events()
            self.update(dt)
            self.draw()
        self.capture_mouse(False)
        pygame.quit()


if __name__ == "__main__":
    try:
        Game().run()
    except Exception as exc:
        # Visible error instead of a silently disappearing EXE.
        import traceback
        print(traceback.format_exc())
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Arena Duel – Fehler", str(exc))
        except Exception:
            pass
        sys.exit(1)
