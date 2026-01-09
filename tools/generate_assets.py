import pygame
import os

def create_assets():
    pygame.init()
    
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Create a generic white car (facing right)
    # Size: 60x30
    car_surf = pygame.Surface((60, 30), pygame.SRCALPHA)
    # Body
    pygame.draw.rect(car_surf, (255, 255, 255), (0, 10, 60, 20), border_radius=5)
    # Cabin
    pygame.draw.rect(car_surf, (200, 200, 255), (15, 0, 30, 15), border_radius=5)
    # Wheels
    pygame.draw.circle(car_surf, (50, 50, 50), (15, 30), 8)
    pygame.draw.circle(car_surf, (50, 50, 50), (45, 30), 8)
    
    pygame.image.save(car_surf, os.path.join(assets_dir, 'car.png'))
    print("Created car.png")

    # 2. Finish Line Texture
    # Size: 20x100 (vertical strip)
    finish_surf = pygame.Surface((20, 100))
    finish_surf.fill((255, 255, 255))
    check_size = 10
    for y in range(0, 100, check_size):
        for x in range(0, 20, check_size):
            if (x // check_size + y // check_size) % 2 == 0:
                pygame.draw.rect(finish_surf, (0, 0, 0), (x, y, check_size, check_size))
                
    pygame.image.save(finish_surf, os.path.join(assets_dir, 'finish_line.png'))
    print("Created finish_line.png")
    
    pygame.quit()

if __name__ == "__main__":
    create_assets()
