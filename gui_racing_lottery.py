import pygame
import csv
import random
import sys
import math
import os

# --- Configuration ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
GOLD = (255, 215, 0)
UI_BG = (0, 0, 0, 180)

# Game Settings
TRACK_LENGTH = 10000  # Virtual pixels
FINISH_LINE_X = 9000
MIN_SPEED = 5
MAX_SPEED = 20

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

def load_image(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        # Fallback surface if file missing
        surf = pygame.Surface((30, 30))
        surf.fill(RED)
        return surf

class Racer:
    def __init__(self, name, lane_index, total_lanes, color):
        self.name = name
        self.course_progress = 0 # 0.0 to 1.0 (start to finish)
        self.lane_index = lane_index
        self.total_lanes = total_lanes
        self.color = color
        
        self.speed = 0
        self.base_speed = random.uniform(0.0005, 0.0008) # Progress per frame
        self.state = "NORMAL" # NORMAL, BOOST, STUMBLE, CRUISE
        self.state_timer = 0
        
        self.finished = False
        self.finish_time = 0
        
        # Load car
        original_car = load_image('car.png')
        self.base_image = pygame.transform.scale(original_car, (40, 20))
        # Tinting
        color_surf = pygame.Surface(self.base_image.get_size()).convert_alpha()
        color_surf.fill(color)
        self.base_image.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        self.current_image = self.base_image
        self.x = 0
        self.y = 0
        self.angle = 0
        
    def update_logic(self, rank, total_racers, leader_progress):
        if self.finished:
            return

        # State Machine for behavior
        self.state_timer -= 1
        if self.state_timer <= 0:
            # Change state more aggressively
            roll = random.random()
            if roll < 0.25: # Increased boost chance
                self.state = "BOOST"
                self.state_timer = random.randint(20, 60)
            elif roll < 0.35: # Stumble chance
                self.state = "STUMBLE"
                self.state_timer = random.randint(20, 60)
            elif roll < 0.38: # SUPER BOOST chance (Rocket from behind)
                self.state = "SUPER_BOOST"
                self.state_timer = random.randint(40, 80)
            else:
                self.state = "NORMAL"
                self.state_timer = random.randint(30, 90)

        # Calculate Speed Modifiers (Rubber Banding)
        target_speed = self.base_speed
        
        if self.state == "BOOST":
            target_speed *= 1.8
        elif self.state == "SUPER_BOOST":
            target_speed *= 3.0
        elif self.state == "STUMBLE":
            target_speed *= 0.3
        
        # Aggressive Rubber Banding:
        # Distance logic: "In and out of screen"
        # If far behind leader, massive speed up. If leading, massive slow down.
        
        dist_to_leader = leader_progress - self.course_progress
        
        if rank == 0: # Leader
             # Limit holding the lead
             target_speed *= 0.65 
        elif rank < 3: # Constant pressure on top 3
             target_speed *= 0.85
        elif dist_to_leader > 0.15: # If fallen well behind camera
             target_speed *= 3.0 # Zoom back into frame
        elif dist_to_leader > 0.05:
             target_speed *= 1.5
             
        # Add pure noise for jittery excitement
        target_speed *= random.uniform(0.8, 1.2)

        self.speed += (target_speed - self.speed) * 0.08 # Snappier acceleration
        self.course_progress += self.speed
        
        if self.course_progress >= 1.0:
            self.course_progress = 1.0
            self.finished = True

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Lottery Racing League")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.ui_font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 64)
        
        self.finish_texture = load_image('finish_line.png')
        self.background_texture = load_image('background.png') # Load background
        self.road_texture = load_image('road.png') # Load road texture
        self.start_texture = load_image('start_line.png') # Load start line texture


        self.contestants = self.load_contestants("contestants.csv")
        self.racers = []
        
        self.state = "START_MENU" # START_MENU, RACING, FINISHED
        
        self.track_points = self.generate_track_points()
        self.camera_offset = [0, 0]
        self.zoom_level = 1.0

        # Generate Full Track Surface
        print("Generating track texture...")
        self.track_surface = self.generate_full_track_texture()

    def generate_full_track_texture(self):
        # Determine bounds
        max_x = 15000 + 500
        # Increase surface height to avoid clipping. Add padding.
        Y_PADDING = 800
        height = SCREEN_HEIGHT + 2 * Y_PADDING
        
        # 1. Create Tiled Road Texture
        # We make a surface large enough to hold the track
        full_surf = pygame.Surface((max_x, height), pygame.SRCALPHA)
        
        # Tile the road texture across the entire surface
        # Assuming road_texture is seamlessly tileable
        rw, rh = self.road_texture.get_size()
        for x in range(0, max_x, rw):
            for y in range(0, height, rh):
                full_surf.blit(self.road_texture, (x, y))
        
        # 2. Create Mask
        mask_surf = pygame.Surface((max_x, height), pygame.SRCALPHA)
        # Fill with transparent
        mask_surf.fill((0, 0, 0, 0))
        
        # Draw the continuous road shape (White, full alpha)
        # Using circles at every point for smoothness
        track_width = 340
        radius = int(track_width / 2)
        
        # Draw circles at vertices for smooth joints
        # Optimizing: Step size 4 is probably fine for circles if radius is large
        # But to be safe for "continuous", do step 2
        for i in range(0, len(self.track_points), 2):
            pt = self.track_points[i]
            # Shift Y coordinate by Y_PADDING to draw on center of tall surface
            draw_y = int(pt[1] + Y_PADDING)
            if draw_y > -radius and draw_y < height + radius:
                 pygame.draw.circle(mask_surf, (255, 255, 255, 255), (int(pt[0]), draw_y), radius)
            
        # Also fill gaps between circles with thick lines to be safe? 
        # With step 2 (100px) and radius 170, circles will overlap heavily, creating a solid worm.    
        
        # 3. Apply Mask to Texture
        # BLEND_RGBA_MULT: Result = Dst * Src
        # Dst = Texture (R,G,B,A), Src = Mask (255,255,255, A_mask) or (0,0,0,0)
        # If Mask is White with Alpha 255: Texture * 1 = Texture
        # If Mask is Transparent (0,0,0,0): Texture * 0 = Transparent
        
        # To make this work, we blit MASK onto TEXTURE.
        full_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return full_surf

    def generate_track_points(self):
        points = []
        # Generate a sine wave track
        length = 15000
        for x in range(0, length, 50):
            # Complex sine wave for interesting curves
            y = SCREEN_HEIGHT // 2 + \
                math.sin(x * 0.002) * 200 + \
                math.sin(x * 0.005) * 100
            points.append((x, y))
        return points

    def get_track_position(self, progress, lane_idx, total_lanes):
        # Map 0.0-1.0 to track length
        total_dist = len(self.track_points) - 2 # Safety buffer
        float_idx = progress * total_dist
        idx = int(float_idx)
        t = float_idx - idx
        
        # Get point and next point for tangent
        p1 = self.track_points[idx]
        p2 = self.track_points[idx + 1]
        
        # Interpolate
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        
        # Tangent angle
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle = math.atan2(dy, dx)
        
        # Lane offset (perpendicular to path)
        # 90 degrees is +PI/2
        perp_angle = angle + math.pi / 2
        
        # Track width is 400
        lane_width = 300 / max(1, total_lanes)
        offset = (lane_idx - total_lanes/2) * lane_width
        
        final_x = x + math.cos(perp_angle) * offset
        final_y = y + math.sin(perp_angle) * offset
        
        return final_x, final_y, -math.degrees(angle)

    def load_contestants(self, filepath):
        names = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # Skip header
                for row in reader:
                    if row:
                        names.append(row[0])
        except Exception as e:
            print(f"Error loading CSV: {e}")
            names = [f"Racer {i}" for i in range(1, 21)]
        return names[:30] 

    def start_race(self):
        self.racers = []
        self.finished_racers = []
        self.winner = None
        self.state = "RACING"
        
        lanes = len(self.contestants)
        for i, name in enumerate(self.contestants):
            color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            self.racers.append(Racer(name, i, lanes, color))       

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "START_MENU":
                    # Simple Start Button Region
                    mx, my = pygame.mouse.get_pos()
                    btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50, 200, 100)
                    if btn_rect.collidepoint(mx, my):
                         self.start_race()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.state == "FINISHED":
                    self.state = "START_MENU"

    def update(self):
        if self.state == "RACING":
            all_finished = True
            
            if not self.racers: return

            # Sort by progress to determine rank
            sorted_racers = sorted(self.racers, key=lambda r: r.course_progress, reverse=True)
            leader_prog = sorted_racers[0].course_progress
            
            for i, racer in enumerate(self.racers):
                # We need the racer's rank. Racer is 'racer', find its index in sorted_racers
                rank = sorted_racers.index(racer)
                
                if not racer.finished:
                    racer.update_logic(rank, len(self.racers), leader_prog)
                    if racer.finished:
                        racer.finish_time = pygame.time.get_ticks()
                        self.finished_racers.append(racer)
                        all_finished = False 
                    else:
                        all_finished = False
                
                # Update position for rendering
                rx, ry, rangle = self.get_track_position(racer.course_progress, racer.lane_index, racer.total_lanes)
                racer.x = rx
                racer.y = ry
                racer.angle = rangle
                # Rotate image
                racer.current_image = pygame.transform.rotate(racer.base_image, rangle)

            # Camera logic: Follow leader
            leader = sorted_racers[0]
            target_cam_x = leader.x - SCREEN_WIDTH * 0.4
            target_cam_y = leader.y - SCREEN_HEIGHT * 0.5
            
            self.camera_offset[0] += (target_cam_x - self.camera_offset[0]) * 0.1
            self.camera_offset[1] += (target_cam_y - self.camera_offset[1]) * 0.1

            if len(self.finished_racers) == len(self.racers):
                self.state = "FINISHED"
                self.winner = self.finished_racers[0]
        
        elif self.state == "FINISHED":
            # Smoothly Center on Winner
            if self.winner:
                target_cam_x = self.winner.x - SCREEN_WIDTH * 0.5
                target_cam_y = self.winner.y - SCREEN_HEIGHT * 0.5
                self.camera_offset[0] += (target_cam_x - self.camera_offset[0]) * 0.05
                self.camera_offset[1] += (target_cam_y - self.camera_offset[1]) * 0.05

    def draw_track(self, surface, offset_x, offset_y):
        # Blit the pre-generated track texture
        # Source rectangle: (camera_x, camera_y, width, height)
        # We assume the track surface is at world coordinate (0,0)
        
        src_x = int(offset_x)
        Y_PADDING = 800
        # Shift drawing up by Y_PADDING because the texture center is shifted down by Y_PADDING during generation
        surface.blit(self.track_surface, (-src_x, -int(offset_y) - Y_PADDING))

    def draw(self):
        # self.screen.fill(GREEN) # Replaced with background texture
        
        # Draw Tiled Background
        # Calculate offset modulo texture size to create infinite tiling effect
        bg_w, bg_h = self.background_texture.get_size()
        
        # Determine starting position for tiling
        # We need to cover the screen (0,0) to (WIDTH, HEIGHT)
        # The camera offset shifts the world, so we shift the texture opposite
        
        start_x = -(self.camera_offset[0] % bg_w)
        start_y = -(self.camera_offset[1] % bg_h)
        
        # Tile across screen
        for x in range(int(start_x), SCREEN_WIDTH, bg_w):
            for y in range(int(start_y), SCREEN_HEIGHT, bg_h):
                self.screen.blit(self.background_texture, (x, y))
        
        if self.state == "START_MENU":
            # Draw Start Screen
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0,0))
            
            # Title
            title = self.large_font.render("GRAND PRIX LOTTERY", True, GOLD)
            title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(title, title_rect)
            
            # Start Button
            btn_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50, 200, 100)
            pygame.draw.rect(self.screen, RED, btn_rect, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, btn_rect, 3, border_radius=10)
            
            start_txt = self.ui_font.render("START RACE", True, WHITE)
            txt_rect = start_txt.get_rect(center=btn_rect.center)
            self.screen.blit(start_txt, txt_rect)
            
            # Sidebar List
            # Left panel
            panel_rect = pygame.Rect(50, 200, 300, SCREEN_HEIGHT - 250)
            pygame.draw.rect(self.screen, (30, 30, 30), panel_rect, border_radius=5)
            
            header = self.ui_font.render("Contestants", True, WHITE)
            self.screen.blit(header, (60, 210))
            
            for i, name in enumerate(self.contestants):
                if 250 + i * 20 > SCREEN_HEIGHT - 60: break # Clip
                txt = self.font.render(f"{i+1}. {name}", True, (200, 200, 200))
                self.screen.blit(txt, (60, 250 + i * 20))
                
        elif self.state in ["RACING", "FINISHED"]:
            # Virtual Camera Rendering
            
            # 1. Draw Track
            self.draw_track(self.screen, self.camera_offset[0], self.camera_offset[1])
            
            # 2. Draw Start/Finish Lines
            # Start
            start_x, start_y, start_angle = self.get_track_position(0, 0, 0)
            s_screen_x = start_x - self.camera_offset[0]
            s_screen_y = start_y - self.camera_offset[1]
            
            if -100 < s_screen_x < SCREEN_WIDTH + 100 and -100 < s_screen_y < SCREEN_HEIGHT + 100:
                # Scale start line to track width
                # Track width is 340, start line texture might be different
                start_img = pygame.transform.scale(self.start_texture, (50, 360)) # Sizing similar to finish line
                start_img = pygame.transform.rotate(start_img, start_angle)
                start_rect = start_img.get_rect(center=(s_screen_x, s_screen_y))
                self.screen.blit(start_img, start_rect)

            # Finish
            end_x, end_y, end_angle = self.get_track_position(1.0, 0, 0)
            e_screen_x = end_x - self.camera_offset[0]
            e_screen_y = end_y - self.camera_offset[1]
            
            if -100 < e_screen_x < SCREEN_WIDTH + 100 and -100 < e_screen_y < SCREEN_HEIGHT + 100:
                # Scale finish line
                finish_img = pygame.transform.scale(self.finish_texture, (50, 360))
                finish_img = pygame.transform.rotate(finish_img, end_angle)
                finish_rect = finish_img.get_rect(center=(e_screen_x, e_screen_y))
                self.screen.blit(finish_img, finish_rect)
            
            # Draw Racers
            # Draw from top to bottom (y-sorting) for psuedo-depth doesn't matter much top-down
            # But order matters if overlapping
            for racer in self.racers:
                screen_x = racer.x - self.camera_offset[0]
                screen_y = racer.y - self.camera_offset[1]
                
                if -50 < screen_x < SCREEN_WIDTH + 50 and -50 < screen_y < SCREEN_HEIGHT + 50:
                    rect = racer.current_image.get_rect(center=(screen_x, screen_y))
                    self.screen.blit(racer.current_image, rect)
                    
                    # Name Tag
                    tag = self.font.render(racer.name, True, WHITE)
                    self.screen.blit(tag, (screen_x + 20, screen_y - 20))

            # 3. UI Overlay
            # Leaderboard
            board_rect = pygame.Rect(20, 20, 250, 200)
            s = pygame.Surface((250, 200), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, board_rect)
            
            head = self.ui_font.render("Leaderboard", True, GOLD)
            self.screen.blit(head, (30, 25))
            
            live_rank = sorted(self.racers, key=lambda r: (-r.finished, -r.course_progress))
            for i, racer in enumerate(live_rank[:8]):
                txt = self.font.render(f"{i+1}. {racer.name}", True, WHITE if i > 0 else GOLD)
                self.screen.blit(txt, (30, 55 + i * 20))

            if self.state == "FINISHED" and self.winner:
                 # Victory Text
                 text = self.large_font.render(f"WINNER: {self.winner.name}", True, GOLD)
                 # Shadow
                 text_shad = self.large_font.render(f"WINNER: {self.winner.name}", True, BLACK)
                 
                 cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
                 r = text.get_rect(center=(cx, cy))
                 rs = text_shad.get_rect(center=(cx+2, cy+2))
                 
                 self.screen.blit(text_shad, rs)
                 self.screen.blit(text, r)
                 
                 sub = self.ui_font.render("Press 'R' for Menu", True, WHITE)
                 self.screen.blit(sub, sub.get_rect(center=(cx, cy + 60)))

        pygame.display.flip()



    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()
