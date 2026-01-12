import random
import pygame
import os

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

def load_image(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        # Fallback surface if file missing
        surf = pygame.Surface((30, 30))
        surf.fill((200, 50, 50))
        return surf

class Racer:
    def __init__(self, name, lane_index, total_lanes, color, duration_multiplier=1.0):
        self.name = name
        self.course_progress = 0 # 0.0 to 1.0 (start to finish)
        self.lane_index = lane_index
        self.total_lanes = total_lanes
        self.color = color
        
        self.speed = 0
        # If duration_multiplier is higher (longer race), speed should be lower.
        self.base_speed = random.uniform(0.0005, 0.0008) / max(0.1, duration_multiplier) 
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
        self.visual_angle_offset = 0
        
    def update_logic(self, rank, total_racers, leader_progress, settings=None):
        if self.finished:
            return

        # Crash Settings
        crash_chance = 0
        crash_cooldown = 60
        if settings:
             crash_chance = settings.get("car_crash_chance", 0.003)
             # Convert ms to frames roughly (60 fps)
             crash_cooldown = int(settings.get("car_crash_cooldown", 2000) / 1000 * 60)

        # Handle CRASHED state
        if self.state == "CRASHED":
             self.speed *= 0.9 # Rapid deceleration
             self.visual_angle_offset += 25 # Spin
             self.state_timer -= 1
             
             # Still move a little bit based on momentum
             self.course_progress += self.speed
             if self.course_progress >= 1.0:
                self.course_progress = 1.0
                self.finished = True
                
             if self.state_timer <= 0:
                 self.state = "NORMAL"
                 self.visual_angle_offset = 0
                 # Give a small recovery boost or just reset behavior
                 self.state_timer = 60
             return

        # Random Crash Trigger
        if self.state != "FINISHED" and random.random() < crash_chance:
            self.state = "CRASHED"
            self.state_timer = crash_cooldown
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