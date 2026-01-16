import pygame
import csv
import random
import sys
import math
import os
import json
from racer import Racer
# --- Configuration ---
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
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), 'sound_effects')


def load_image(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        # Fallback surface if file missing
        surf = pygame.Surface((30, 30))
        surf.fill(RED)
        return surf

class Game:
    def __init__(self):
        pygame.init()
        self.settings = self.load_settings()
        self.screen_width = self.settings.get("screen_width", 1920)
        self.screen_height = self.settings.get("screen_height", 1080)

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Lottery Racing League")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.ui_font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 64)
        self.winner_font = pygame.font.SysFont("Arial", 120)  # Bigger font for winner
        
        self.finish_texture = load_image('finish_line.png')
        self.background_texture = load_image('background.png') # Load background
        self.road_texture = load_image('road.png') # Load road texture
        self.sidewalk_texture = load_image('sidewalk.png') # Load sidewalk texture
        self.banner_texture = load_image('siewalk_banner.png') # Load banner texture
        self.start_texture = load_image('start_line.png') # Load start line texture

        # Load Sounds
        self.crash_sound = None
        self.boost_sound = None
        
        if os.path.exists(os.path.join(SOUNDS_DIR, 'car-crashed.wav')):
            try:
                self.crash_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'car-crashed.wav'))
                self.crash_sound.set_volume(0.4)
            except Exception as e:
                print(f"Failed to load crash sound: {e}")

        if os.path.exists(os.path.join(SOUNDS_DIR, 'car-boosted.wav')):
            try:
                self.boost_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'car-boosted.wav'))
                self.boost_sound.set_volume(0.4)
            except Exception as e:
                print(f"Failed to load boost sound: {e}")

        self.countdown_sound = None
        self.start_sound = None
        self.finish_sound = None

        if os.path.exists(os.path.join(SOUNDS_DIR, 'countdown.wav')):
            try:
                self.countdown_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'countdown.wav'))
            except Exception as e:
                print(f"Failed to load countdown sound: {e}")

        if os.path.exists(os.path.join(SOUNDS_DIR, 'car-starting.wav')):
            try:
                self.start_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'car-starting.wav'))
            except Exception as e:
                print(f"Failed to load car-starting sound: {e}")

        if os.path.exists(os.path.join(SOUNDS_DIR, 'finish-race.wav')):
            try:
                self.finish_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'finish-race.wav'))
            except Exception as e:
                print(f"Failed to load finish-race sound: {e}")

        self.bg_music_path = os.path.join(SOUNDS_DIR, 'background-music.mp3')
        if not os.path.exists(self.bg_music_path):
            self.bg_music_path = None

        # Load Close Button
        self.close_btn = load_image('button-close.png')
        # Scale to a reasonable size
        cw, ch = self.close_btn.get_size()
        target_w = 100
        scale = target_w / cw
        self.close_btn = pygame.transform.scale(self.close_btn, (int(cw * scale), int(ch * scale)))
        self.close_btn_rect = self.close_btn.get_rect()
        self.close_btn_rect.topright = (self.screen_width - 20, 20)

        # Load Menu Buttons
        self.start_btn_img = load_image('button-start_race.png')
        sw, sh = self.start_btn_img.get_size()
        target_w = 300
        scale = target_w / sw
        self.start_btn_img = pygame.transform.scale(self.start_btn_img, (int(sw * scale), int(sh * scale)))
        self.start_btn_rect = self.start_btn_img.get_rect(center=(self.screen_width//2, self.screen_height//2))

        self.restart_btn_img = load_image('button-restart_race.png')
        rw, rh = self.restart_btn_img.get_size()
        scale = target_w / rw
        self.restart_btn_img = pygame.transform.scale(self.restart_btn_img, (int(rw * scale), int(rh * scale)))
        self.restart_btn_rect = self.restart_btn_img.get_rect(center=(self.screen_width//2, self.screen_height - 150))

        self.contestants = self.load_contestants("contestants.csv")
        self.racers = []
        
        # Calculate dynamic track width based on contestant count
        # Ensure enough space for at least 50 racers
        self.track_width = max(340, len(self.contestants) * 15)
        self.drivable_width = self.track_width - 40

        self.state = "START_MENU" # START_MENU, RACING, FINISHED
        self.scroll_y = 0  # Scroll position for contestant list
        
        self.track_points = self.generate_track_points()
        self.camera_offset = [0, 0]
        self.zoom_level = 1.0

        # Shadows & Obstacles
        self.obstacles = [] # list of dicts: {progress, lane, image, x, y}
        self.obstacle_images = []
        obs_dir = os.path.join(ASSETS_DIR, 'random_obstacle')
        
        # Get obstacle size from settings (default 40)
        obs_size = self.settings.get("obstacle_size", 40)
        
        if os.path.exists(obs_dir):
            for f in os.listdir(obs_dir):
                 if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                     img = pygame.image.load(os.path.join(obs_dir, f)).convert_alpha()
                     # Scale obstacle
                     img = pygame.transform.scale(img, (obs_size, obs_size))
                     self.obstacle_images.append(img)

        # Boosters
        self.boosters = [] # list of dicts: {progress, lane, image, x, y}
        self.booster_images = []
        boost_dir = os.path.join(ASSETS_DIR, 'random_booster')
        boost_size = self.settings.get("booster_size", 40)
        
        if os.path.exists(boost_dir):
            for f in os.listdir(boost_dir):
                 if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                     img = pygame.image.load(os.path.join(boost_dir, f)).convert_alpha()
                     img = pygame.transform.scale(img, (boost_size, boost_size))
                     self.booster_images.append(img)

        # Load random photos
        self.random_photos = self.load_random_photos()

        # Generate Full Track Surface
        print("Generating track texture...")
        self.track_surface = self.generate_full_track_texture()

    def load_random_photos(self):
        photos = []
        photos_dir = os.path.join(ASSETS_DIR, 'random_photos')
        if os.path.exists(photos_dir):
            for f in os.listdir(photos_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                     try:
                         # Load and scale down a bit if too large
                         img = pygame.image.load(os.path.join(photos_dir, f)).convert_alpha()
                         w, h = img.get_size()
                         target_size = self.settings.get("random_photos_max_size", 600)
                         if w > target_size or h > target_size:
                            scale = target_size / max(w, h)
                            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
                         photos.append(img)
                     except Exception as e:
                         print(f"Failed to load photo {f}: {e}")
        return photos

    def generate_full_track_texture(self):
        # Determine bounds
        max_x = 15000 + 500
        # Increase height to avoid clipping. Add padding.
        Y_PADDING = 800
        height = self.screen_height + 2 * Y_PADDING
        
        # 1. Create Tiled Road Texture
        # We make a surface large enough to hold the track
        road_surf = pygame.Surface((max_x, height), pygame.SRCALPHA)
        
        # Tile the road texture across the entire surface
        # Assuming road_texture is seamlessly tileable
        rw, rh = self.road_texture.get_size()
        for x in range(0, max_x, rw):
            for y in range(0, height, rh):
                road_surf.blit(self.road_texture, (x, y))

        # 1b. Create Tiled Sidewalk Texture
        sidewalk_surf = pygame.Surface((max_x, height), pygame.SRCALPHA)
        sw, sh = self.sidewalk_texture.get_size()
        for x in range(0, max_x, sw):
            for y in range(0, height, sh):
                # Tint slightly for variety? Optional.
                sidewalk_surf.blit(self.sidewalk_texture, (x, y))

        # 1c. Create Banner Layer (Placed along track)
        banner_layer = pygame.Surface((max_x, height), pygame.SRCALPHA)
        
        # Logic to place banners along the spline
        track_width = self.track_width
        road_radius = int(track_width / 2)
        sidewalk_width_extra = 40
        sidewalk_radius = road_radius + sidewalk_width_extra
        
        # --- Sprinkle Random Photos ---
        if self.random_photos:
            photo_layer = pygame.Surface((max_x, height), pygame.SRCALPHA)
            # We will walk along the track and randomly place photos
            # Similar to banner logic but purely random
            
            p_points = self.track_points
            offset_val = self.settings.get("random_photos_offset", 30)
            safe_dist = sidewalk_radius + offset_val # Minimum distance from center
            max_dist = safe_dist + 300 # Maximum distance from center
            
            # Use accumulated distance to space them out somewhat evenly or just random?
            # User said "sprinkle ... can be at random location"
            # Let's place one every ~200-500 pixels of track length
            
            freq_base = self.settings.get("random_photos_interval", self.settings.get("random_photos_frequency", 500))
            # Ensure safe bounds
            if freq_base < 50: freq_base = 50

            current_dist = 0
            next_photo_dist = random.randint(int(freq_base * 0.5), int(freq_base * 1.5))
            
            for i in range(0, len(p_points) - 1):
                p1 = p_points[i]
                p2 = p_points[i+1]
                
                seg_dx = p2[0] - p1[0]
                seg_dy = p2[1] - p1[1]
                seg_len = math.sqrt(seg_dx*seg_dx + seg_dy*seg_dy)
                
                current_dist += seg_len
                
                if current_dist >= next_photo_dist:
                    current_dist = 0
                    next_photo_dist = random.randint(int(freq_base * 0.5), int(freq_base * 1.5)) # Space them out
                    
                    # Place a photo
                    photo = random.choice(self.random_photos)
                    
                    # Random rotation and scale variation
                    base_scale = self.settings.get("random_photos_scale", 1.0)
                    scale_var = random.uniform(0.8, 1.2) * base_scale
                    w, h = photo.get_size()
                    t_photo = pygame.transform.scale(photo, (int(w * scale_var), int(h * scale_var)))
                    # t_photo = pygame.transform.rotate(t_photo, random.randint(0, 360)) # No rotation requested
                    
                    # Calculate position
                    # Random side
                    side = 1 if random.random() > 0.5 else -1
                    dist = random.uniform(safe_dist, max_dist)
                    
                    angle = math.atan2(seg_dy, seg_dx)
                    perp_angle = angle + math.pi / 2
                    
                    draw_x = p1[0]
                    draw_y = p1[1] + Y_PADDING
                    
                    px = draw_x + math.cos(perp_angle) * dist * side
                    py = draw_y + math.sin(perp_angle) * dist * side
                    
                    p_rect = t_photo.get_rect(center=(int(px), int(py)))
                    
                    # Blit to banner_layer (which is the bottom layer for props)
                    banner_layer.blit(t_photo, p_rect)

        # Place banner center right at the edge of the sidewalk
        # Drawing order will hide the inner half
        offset_dist = sidewalk_radius + 15 # Slight text offset
        
        banner_dist_setting = self.settings.get("banner_distance", 50)
        banner_scale_setting = self.settings.get("banner_scale", 1.0)
        
        # Scale the banner texture
        bw, bh = self.banner_texture.get_size()
        scaled_banner = pygame.transform.scale(self.banner_texture, (int(bw * banner_scale_setting), int(bh * banner_scale_setting)))
        
        points = self.track_points
        # Step through points. If points are 50px apart, we render a banner at each or interpolate.
        
        accumulated_dist = 0
        last_banner_dist = -banner_dist_setting # Force first one to draw? Or start at 0
        
        for i in range(0, len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            # Distance of this segment
            seg_dx = p2[0] - p1[0]
            seg_dy = p2[1] - p1[1]
            seg_len = math.sqrt(seg_dx*seg_dx + seg_dy*seg_dy)
            
            accumulated_dist += seg_len
            
            if accumulated_dist - last_banner_dist >= banner_dist_setting:
                last_banner_dist = accumulated_dist
                
                # Midpoint for smoother placement (or p1)
                # Using p1 since we just crossed threshold
                
                # Angle of segment
                angle = math.atan2(seg_dy, seg_dx)
                perp_angle = angle + math.pi / 2
                
                # Draw coords (add Padding)
                draw_x = p1[0]
                draw_y = p1[1] + Y_PADDING
                
                # Rotate banner (Convert radians to degrees, negative for pygame)
                deg = -math.degrees(angle)
                rot_img = pygame.transform.rotate(scaled_banner, deg)
                
                # Left Side Banner
                lx = draw_x + math.cos(perp_angle) * offset_dist
                ly = draw_y + math.sin(perp_angle) * offset_dist
                l_rect = rot_img.get_rect(center=(int(lx), int(ly)))
                banner_layer.blit(rot_img, l_rect)
                
                # Right Side Banner
                rx = draw_x - math.cos(perp_angle) * offset_dist
                ry = draw_y - math.sin(perp_angle) * offset_dist
                r_rect = rot_img.get_rect(center=(int(rx), int(ry)))
                banner_layer.blit(rot_img, r_rect)
        
        # 2. Create Masks for Road and Sidewalk
        road_mask = pygame.Surface((max_x, height), pygame.SRCALPHA)
        road_mask.fill((0, 0, 0, 0))

        sidewalk_mask = pygame.Surface((max_x, height), pygame.SRCALPHA)
        sidewalk_mask.fill((0, 0, 0, 0))

        # We don't need a banner mask anymore since we draw it explicitly
        
        # Draw the continuous road shape
        # Draw circles at vertices for smooth joints
        for i in range(0, len(self.track_points), 2):
            pt = self.track_points[i]
            draw_y = int(pt[1] + Y_PADDING)
            if draw_y > -sidewalk_radius and draw_y < height + sidewalk_radius:
                 pygame.draw.circle(sidewalk_mask, (255, 255, 255, 255), (int(pt[0]), draw_y), sidewalk_radius)
                 pygame.draw.circle(road_mask, (255, 255, 255, 255), (int(pt[0]), draw_y), road_radius)
            
        # 3. Apply Mask to Texture
        
        # Apply masks
        sidewalk_surf.blit(sidewalk_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        road_surf.blit(road_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Combine: 
        # Bottom: Banner Layer
        # Middle: Sidewalk
        # Top: Road
        
        final_surf = banner_layer
        final_surf.blit(sidewalk_surf, (0, 0))
        final_surf.blit(road_surf, (0, 0))
        
        return final_surf

    def generate_track_points(self):
        points = []
        # Generate a sine wave track
        length = 15000
        for x in range(0, length, 50):
            # Ease in the curves so the start is straight
            # The start line is not tilted
            curve_intensity = min(1.0, x / 1500.0)
            
            # Complex sine wave for interesting curves
            y = self.screen_height // 2 + \
                (math.sin(x * 0.002) * 200 + \
                math.sin(x * 0.005) * 100) * curve_intensity
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
        
        # Track width is dynamic
        lane_width = self.drivable_width / max(1, total_lanes)
        offset = (lane_idx - total_lanes/2) * lane_width
        
        final_x = x + math.cos(perp_angle) * offset
        final_y = y + math.sin(perp_angle) * offset
        
        return final_x, final_y, -math.degrees(angle)

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {
                "race_duration_multiplier": 1.0,
                "random_photos_interval": 500,
                "random_photos_scale": 1.0,
                "random_photos_offset": 30,
                "screen_width": 1920,
                "screen_height": 1080,
                "random_image_max_size": 600,
                "winning_car_zoom": 1.5,
                "banner_distance": 50,
                "banner_scale": 1.0
            }

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
            
        random.shuffle(names)
        return names[:60] 

    def start_race(self):
        self.racers = []
        self.obstacles = [] # Reset obstacles
        self.boosters = [] # Reset boosters
        self.finished_racers = []
        self.winner = None
        self.state = "COUNTDOWN"
        self.countdown_start = pygame.time.get_ticks()
        
        if self.countdown_sound:
            self.countdown_sound.play()
        
        dur_mult = float(self.settings.get("race_duration_multiplier", 1.0))
        
        num_racers = len(self.contestants)
        for i, name in enumerate(self.contestants):
            hue = i / max(1, num_racers)
            color = pygame.Color(0)
            color.hsva = ((hue * 360) % 360, 100, 100, 100)
            
            r = Racer(name, i, num_racers, color, dur_mult)
            rx, ry, rangle = self.get_track_position(0, i, num_racers)
            r.x = rx
            r.y = ry
            r.angle = rangle
            self.racers.append(r)
            
        sx, sy, _ = self.get_track_position(0, 0, 1)
        self.camera_offset = [sx - self.screen_width * 0.4, sy - self.screen_height * 0.5]
        self.zoom_level = 1.0

    def reset_to_menu(self):
        if self.winner and self.winner.name in self.contestants:
            self.contestants.remove(self.winner.name)
        self.state = "START_MENU"
        self.zoom_level = 1.0
        self.winner = None
        self.racers = []
        self.finished_racers = []
        self.scroll_y = 0

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # Check Close Button Click
                if self.close_btn_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

                if self.state == "START_MENU":
                    # Simple Start Button Region
                    # mx, my = pygame.mouse.get_pos() # Already got above
                    if self.start_btn_rect.collidepoint(mx, my):
                         self.start_race()

                if self.state == "FINISHED":
                     if self.restart_btn_rect.collidepoint(mx, my):
                         self.reset_to_menu()

            if event.type == pygame.MOUSEWHEEL:
                if self.state == "START_MENU":
                    mx, my = pygame.mouse.get_pos()
                    panel_rect = pygame.Rect(50, 200, 300, self.screen_height - 250)
                    if panel_rect.collidepoint(mx, my):
                         self.scroll_y -= event.y * 20
                         total_height = len(self.contestants) * 20
                         visible_height = panel_rect.height - 50
                         max_scroll = max(0, total_height - visible_height)
                         self.scroll_y = max(0, min(self.scroll_y, max_scroll))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.state == "FINISHED":
                    self.reset_to_menu()

    def update(self):
        if self.state == "COUNTDOWN":
            now = pygame.time.get_ticks()
            if now - self.countdown_start > 3000:
                self.state = "RACING"
                if self.start_sound:
                    self.start_sound.play()
                
                if self.bg_music_path:
                    try:
                        pygame.mixer.music.load(self.bg_music_path)
                        pygame.mixer.music.set_volume(0.3)
                        pygame.mixer.music.play(-1)
                    except Exception as e:
                        print(f"Failed to play background music: {e}")
        
        elif self.state == "RACING":
            all_finished = True
            
            if not self.racers: return

            # Sort by progress to determine rank
            sorted_racers = sorted(self.racers, key=lambda r: r.course_progress, reverse=True)
            leader_prog = sorted_racers[0].course_progress
            
            for i, racer in enumerate(self.racers):
                # We need the racer's rank. Racer is 'racer', find its index in sorted_racers
                rank = sorted_racers.index(racer)
                
                if not racer.finished:
                    racer.update_logic(rank, len(self.racers), leader_prog, self.settings)
                    
                    # Handle Obstacle Generation requested by racer
                    if getattr(racer, 'wants_obstacle', False) and self.obstacle_images:
                        racer.wants_obstacle = False
                        
                        # Get distance from settings (default 1000 virtual pixels)
                        gen_dist = self.settings.get("obstacle_generate_distance", 1000)
                        
                        # Track is approx 15000 units long (from generate_track_points)
                        # Convert pixel distance to progress (0.0 - 1.0)
                        dist_inc = gen_dist / 15000.0
                        
                        # Add slight variance to prevent obvious patterns if multiple spawn?
                        # dist_inc *= random.uniform(0.9, 1.1)

                        obs_prog = min(0.99, racer.course_progress + dist_inc)
                        
                        ox, oy, _ = self.get_track_position(obs_prog, racer.lane_index, racer.total_lanes)
                        img = random.choice(self.obstacle_images)
                        
                        self.obstacles.append({
                            'progress': obs_prog,
                            'lane': racer.lane_index,
                            'image': img,
                            'x': ox,
                            'y': oy
                        })

                    # Handle Booster Generation
                    if getattr(racer, 'wants_boost', False) and self.booster_images:
                        racer.wants_boost = False
                        
                        gen_dist = self.settings.get("booster_generate_distance", 1000)
                        dist_inc = gen_dist / 15000.0
                        boost_prog = min(0.99, racer.course_progress + dist_inc)
                        
                        bx, by, _ = self.get_track_position(boost_prog, racer.lane_index, racer.total_lanes)
                        img = random.choice(self.booster_images)
                        
                        self.boosters.append({
                            'progress': boost_prog,
                            'lane': racer.lane_index,
                            'image': img,
                            'x': bx,
                            'y': by
                        })

                    if racer.finished:
                        racer.finish_time = pygame.time.get_ticks()
                        self.finished_racers.append(racer)
                        all_finished = False 
                    else:
                        all_finished = False
                
                # Update position for rendering
                rx, ry, rangle = self.get_track_position(racer.course_progress, racer.lane_index, racer.total_lanes)
                racer.x, racer.y, racer.angle = rx, ry, rangle + getattr(racer, 'visual_angle_offset', 0)

                # Check Obstacle Collisions
                if not racer.finished and racer.state != "CRASHED":
                     # Simple distance check based on object size
                     hitbox_size = self.settings.get("obstacle_size", 40) * 0.7 # slightly forgiving
                     
                     for obs in self.obstacles[:]:
                         dx = racer.x - obs['x']
                         dy = racer.y - obs['y']
                         if abs(dx) < hitbox_size and abs(dy) < hitbox_size: # Hitbox
                             if hasattr(racer, 'crash'):
                                 racer.crash()
                                 if self.crash_sound: self.crash_sound.play()
                             # Remove obstacle so others don't hit the same one immediately (or leave it?)
                             # Getting rid of it avoids multiple crashes on same frame or confusing clutter
                             self.obstacles.remove(obs)
                             break
                
                # Check Booster Collisions
                if not racer.finished and racer.state != "CRASHED":
                     hitbox_size = self.settings.get("booster_size", 40) * 0.8
                     
                     for boost in self.boosters[:]:
                         dx = racer.x - boost['x']
                         dy = racer.y - boost['y']
                         if abs(dx) < hitbox_size and abs(dy) < hitbox_size:
                             if hasattr(racer, 'boost'):
                                 racer.boost()
                                 if self.boost_sound: self.boost_sound.play()
                             self.boosters.remove(boost)
                             break
            
            if self.racers:
                leader = sorted_racers[0]
                target_cam_x = leader.x - self.screen_width * 0.4
                target_cam_y = leader.y - self.screen_height * 0.5
                
                self.camera_offset[0] += (target_cam_x - self.camera_offset[0]) * 0.1
                self.camera_offset[1] += (target_cam_y - self.camera_offset[1]) * 0.1

            if len(self.finished_racers) == len(self.racers):
                self.state = "FINISHED"
                self.winner = self.finished_racers[0]
                if self.finish_sound:
                    self.finish_sound.play()
                pygame.mixer.music.stop()
        
        elif self.state == "FINISHED":
            # Smoothly Center on Winner and Zoom
            if self.winner:
                # With zoom, we need to center carefully.
                # If zoom is 2.0, the "screen" is half size.
                current_w = self.screen_width / self.zoom_level
                current_h = self.screen_height / self.zoom_level
                
                target_cam_x = self.winner.x - current_w * 0.5
                target_cam_y = self.winner.y - current_h * 0.5
                
                self.camera_offset[0] += (target_cam_x - self.camera_offset[0]) * 0.05
                self.camera_offset[1] += (target_cam_y - self.camera_offset[1]) * 0.05

                # Zoom logic
                target_zoom = self.settings.get("winning_car_zoom", 1.5)
                self.zoom_level += (target_zoom - self.zoom_level) * 0.04
        
    def draw_track(self, surface, cam_x, cam_y):
        # Track surface generated with extra Y_PADDING of 800
        dest_x = 0 - cam_x
        dest_y = -800 - cam_y
        surface.blit(self.track_surface, (dest_x, dest_y))

    def draw(self):
        # We handle zooming by rendering to a temporary surface if needed
        # Or more efficiently, we only use a temp surface if zoom != 1.0 (with some epsilon)
        
        target_surf = self.screen
        
        render_width = self.screen_width
        render_height = self.screen_height
        
        should_scale = abs(self.zoom_level - 1.0) > 0.01
        
        if should_scale:
            render_width = int(self.screen_width / self.zoom_level)
            render_height = int(self.screen_height / self.zoom_level)
            # Create temp surface (optimize by reusing?)
            # For now create new to stay simple
            target_surf = pygame.Surface((render_width, render_height))
        
        # Draw Tiled Background
        # Calculate offset modulo texture size to create infinite tiling effect
        bg_w, bg_h = self.background_texture.get_size()
        
        # Determine starting position for tiling
        start_x = -(self.camera_offset[0] % bg_w)
        start_y = -(self.camera_offset[1] % bg_h)
        
        # Tile across render surface
        for x in range(int(start_x), render_width, bg_w):
            for y in range(int(start_y), render_height, bg_h):
                target_surf.blit(self.background_texture, (x, y))
        
        if self.state == "START_MENU":
            # Draw Start Screen
            if should_scale:
                 # If we are zoomed in on start menu (shouldn't really happen but handle it)
                 # Revert target surf to screen for UI
                 target_surf = self.screen
                 render_width = self.screen_width
                 render_height = self.screen_height

            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0,0))
            
            # Title
            title = self.large_font.render("GRAND PRIX LOTTERY", True, GOLD)
            title_rect = title.get_rect(center=(self.screen_width//2, 100))
            self.screen.blit(title, title_rect)
            
            # Start Button
            self.screen.blit(self.start_btn_img, self.start_btn_rect)
            
            # Sidebar List
            # Left panel
            panel_height = self.screen_height - 250
            panel_rect = pygame.Rect(50, 200, 300, panel_height)
            pygame.draw.rect(self.screen, (30, 30, 30), panel_rect, border_radius=5)
            
            header = self.ui_font.render("Contestants", True, WHITE)
            self.screen.blit(header, (60, 210))
            
            # Clip for scrolling area
            list_start_y = 250
            # Ensure clip rect is within screen bounds
            list_rect = pygame.Rect(50, list_start_y, 300, max(0, panel_height - 50))
            
            # Save current clip
            original_clip = self.screen.get_clip()
            self.screen.set_clip(list_rect)
            
            draw_start_y = list_start_y - self.scroll_y
            
            for i, name in enumerate(self.contestants):
                y_pos = draw_start_y + i * 20
                # Optimization: only draw if touching visible area
                if y_pos + 20 < list_start_y: continue
                if y_pos > 200 + panel_height: break # Below view
                
                txt = self.font.render(f"{i+1}. {name}", True, (200, 200, 200))
                self.screen.blit(txt, (60, y_pos))
            
            # Restore clip
            self.screen.set_clip(original_clip)
                
        elif self.state in ["RACING", "FINISHED", "COUNTDOWN"]:
            # Virtual Camera Rendering
            
            # 1. Draw Track
            self.draw_track(target_surf, self.camera_offset[0], self.camera_offset[1])
            
            # 2. Draw Start/Finish Lines
            # Start
            start_x, start_y, start_angle = self.get_track_position(0, 0, 0)
            s_screen_x = start_x - self.camera_offset[0]
            s_screen_y = start_y - self.camera_offset[1]
            
            if -100 < s_screen_x < render_width + 100 and -100 < s_screen_y < render_height + 100:
                # Scale start line to track width
                # Track width is 340, start line texture might be different
                start_img = pygame.transform.scale(self.start_texture, (50, 360)) # Sizing similar to finish line
                start_img = pygame.transform.rotate(start_img, start_angle)
                start_rect = start_img.get_rect(center=(s_screen_x, s_screen_y))
                target_surf.blit(start_img, start_rect)

            # Finish
            end_x, end_y, end_angle = self.get_track_position(1.0, 0, 0)
            e_screen_x = end_x - self.camera_offset[0]
            e_screen_y = end_y - self.camera_offset[1]
            
            if -100 < e_screen_x < render_width + 100 and -100 < e_screen_y < render_height + 100:
                # Scale finish line
                finish_img = pygame.transform.scale(self.finish_texture, (50, 360))
                finish_img = pygame.transform.rotate(finish_img, end_angle)
                finish_rect = finish_img.get_rect(center=(e_screen_x, e_screen_y))
                target_surf.blit(finish_img, finish_rect)
            
            # Draw Obstacles (Before racers)
            if self.obstacles:
                 for obs in self.obstacles:
                     ox_screen = obs['x'] - self.camera_offset[0]
                     oy_screen = obs['y'] - self.camera_offset[1]
                     if -50 < ox_screen < render_width + 50 and -50 < oy_screen < render_height + 50:
                         img = obs['image']
                         rect = img.get_rect(center=(ox_screen, oy_screen))
                         target_surf.blit(img, rect)

            # Draw Boosters
            if self.boosters:
                 for boost in self.boosters:
                     bx_screen = boost['x'] - self.camera_offset[0]
                     by_screen = boost['y'] - self.camera_offset[1]
                     if -50 < bx_screen < render_width + 50 and -50 < by_screen < render_height + 50:
                         img = boost['image']
                         rect = img.get_rect(center=(bx_screen, by_screen))
                         target_surf.blit(img, rect)

            # Draw Racers
            # Draw from top to bottom (y-sorting) for psuedo-depth doesn't matter much top-down
            # But order matters if overlapping
            for racer in self.racers:
                screen_x = racer.x - self.camera_offset[0]
                screen_y = racer.y - self.camera_offset[1]
                
                if -50 < screen_x < render_width + 50 and -50 < screen_y < render_height + 50:
                    # Rotate the image
                    # Note: Convert angle to degrees. racer.angle seems to be in degrees already based on get_track_position
                    # but Pygame rotates CCW, so we might need to negate if it's not already correct.
                    # get_track_position returns -math.degrees(angle), which is suitable for pygame if angle was math angle.
                    
                    rotated_img = pygame.transform.rotate(racer.current_image, racer.angle)
                    rect = rotated_img.get_rect(center=(screen_x, screen_y))
                    target_surf.blit(rotated_img, rect)
                    
                    # Name Tag
                    tag = self.font.render(racer.name, True, WHITE)
                    target_surf.blit(tag, (screen_x + 20, screen_y - 20))

            # Apply Zoom if needed
            if should_scale:
                scaled_surf = pygame.transform.scale(target_surf, (self.screen_width, self.screen_height))
                self.screen.blit(scaled_surf, (0, 0))
                
            # 3. UI Overlay - ALWAYS draw on direct screen
            # Leaderboard
            board_rect = pygame.Rect(20, 20, 250, 200)
            s = pygame.Surface((250, 200), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, board_rect)
            
            head = self.ui_font.render("Leaderboard", True, GOLD)
            self.screen.blit(head, (30, 25))
            
            # Combine finished racers (in order of finish) with active racers (sorted by progress)
            active_racers = [r for r in self.racers if not r.finished]
            active_racers.sort(key=lambda r: r.course_progress, reverse=True)
            live_rank = self.finished_racers + active_racers
            
            for i, racer in enumerate(live_rank[:8]):
                txt = self.font.render(f"{i+1}. {racer.name}", True, WHITE if i > 0 else GOLD)
                self.screen.blit(txt, (30, 55 + i * 20))

            if self.state == "FINISHED" and self.winner:
                 # Victory Text
                 text = self.winner_font.render(f"WINNER: {self.winner.name}", True, RED)
                 # Shadow
                 text_shad = self.winner_font.render(f"WINNER: {self.winner.name}", True, BLACK)
                 
                 cx, cy = self.screen_width//2, 100
                 r = text.get_rect(center=(cx, cy))
                 rs = text_shad.get_rect(center=(cx+4, cy+4))
                 
                 self.screen.blit(text_shad, rs)
                 self.screen.blit(text, r)
                 
                 sub = self.ui_font.render("Press 'R' for Menu", True, WHITE)
                 self.screen.blit(sub, sub.get_rect(center=(cx, cy + 100)))

                 # Restart Button
                 self.screen.blit(self.restart_btn_img, self.restart_btn_rect)

        if self.state == "COUNTDOWN":
            now = pygame.time.get_ticks()
            timeLeft = 3000 - (now - self.countdown_start)
            if timeLeft > 0:
                seconds = int(timeLeft / 1000) + 1
                txt = str(seconds)
                color = RED
            else:
                txt = "GO!"
                color = GREEN
            
            # Big pulsing text
            font_surf = self.large_font.render(txt, True, color)
            # Scale up
            scale = 3.0
            if timeLeft > 0:
                # Pulse effect
                scale = 3.0 + (timeLeft % 1000) / 500.0
            
            start_w, start_h = font_surf.get_size()
            if scale != 1.0:
                font_surf = pygame.transform.scale(font_surf, (int(start_w * scale), int(start_h * scale)))
                
            rect = font_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(font_surf, rect)

        # Draw UI (Top Layer)
        self.screen.blit(self.close_btn, self.close_btn_rect)

        pygame.display.flip()



    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()
