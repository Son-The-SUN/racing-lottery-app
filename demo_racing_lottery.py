#!/usr/bin/env python3
"""
Demo script for racing lottery game - runs automatically without user input
"""
import sys
import os
import time

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from racing_lottery import RacingGame


def run_demo():
    """Run a quick demo of the racing game."""
    print("\n" + "=" * 70)
    print(" " * 20 + "🎰 LOTTERY RACE DEMO 🎰")
    print("=" * 70)
    print("\nRunning automated demo...\n")
    
    # Create game
    game = RacingGame("contestants.csv")
    
    print(f"Loaded {len(game.contestants)} contestants from CSV")
    print(f"Track length: {game.track_length} units")
    print("\nContestants:")
    for i, name in enumerate(game.contestants, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "=" * 70)
    print("Starting race in 2 seconds...")
    print("=" * 70)
    time.sleep(2)
    
    # Generate tracks
    game.generate_random_tracks()
    
    # Simulate race (faster for demo)
    frame = 0
    while not all(racer.finished for racer in game.racers):
        frame += 1
        game.frame_count = frame
        
        # Move all racers
        for racer in game.racers:
            if not racer.finished:
                racer.move()
                if racer.finished and racer not in [r for _, r in game.winners]:
                    rank = len(game.winners) + 1
                    racer.finish_time = frame
                    game.winners.append((rank, racer))
        
        # Display every 5 frames to speed up demo
        if frame % 5 == 0 or len(game.winners) >= len(game.racers):
            game.display_race()
            time.sleep(0.05)
    
    # Show final results
    time.sleep(1)
    game.display_final_results()
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
