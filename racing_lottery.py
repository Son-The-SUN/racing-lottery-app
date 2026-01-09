"""
Racing Lottery Game - A racing game disguised as a lottery picker.
"""
import csv
import random
import time
import sys
from typing import List, Tuple


class Racer:
    """Represents a contestant in the race."""
    
    def __init__(self, name: str, track_length: int):
        self.name = name
        self.position = 0
        self.track_length = track_length
        self.finished = False
        self.finish_time = None
        
    def move(self) -> None:
        """Move the racer forward by a random amount."""
        if not self.finished:
            # Random movement between 1 and 3 units, with occasional bursts
            movement = random.choices([1, 2, 3, 4], weights=[30, 40, 25, 5])[0]
            self.position += movement
            
            if self.position >= self.track_length:
                self.position = self.track_length
                self.finished = True
    
    def get_display_position(self) -> str:
        """Get the visual representation of the racer's position."""
        progress = int((self.position / self.track_length) * 50)
        track = '=' * progress + '>' + '-' * (50 - progress)
        return f"{self.name:12} [{track}] {self.position}/{self.track_length}"


class RacingGame:
    """Main racing game engine."""
    
    def __init__(self, csv_file: str = "contestants.csv"):
        self.contestants = self.load_contestants(csv_file)
        self.track_length = random.randint(80, 120)
        self.racers: List[Racer] = []
        self.winners: List[Tuple[int, Racer]] = []
        self.frame_count = 0
        
    def load_contestants(self, csv_file: str) -> List[str]:
        """Load contestant names from CSV file."""
        names = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Get the first column value (should be 'Name')
                    name = list(row.values())[0].strip()
                    if name:
                        names.append(name)
        except FileNotFoundError:
            print(f"Error: Could not find {csv_file}")
            sys.exit(1)
        
        if not names:
            print("Error: No contestants found in CSV file")
            sys.exit(1)
            
        return names
    
    def generate_random_tracks(self) -> None:
        """Generate random tracks by shuffling contestants into heats."""
        # Shuffle contestants to create random matchups
        shuffled = self.contestants.copy()
        random.shuffle(shuffled)
        
        # Create racers for all contestants
        self.racers = [Racer(name, self.track_length) for name in shuffled]
    
    def display_race(self) -> None:
        """Display the current state of the race."""
        # Clear screen (works on most terminals)
        print("\033[2J\033[H", end='')
        
        print("=" * 70)
        print(" " * 20 + "🏁 LOTTERY RACE 🏁")
        print("=" * 70)
        print()
        
        # Display all racers
        for racer in self.racers:
            status = "✓" if racer.finished else " "
            print(f"{status} {racer.get_display_position()}")
        
        print()
        print(f"Frame: {self.frame_count}")
        print("=" * 70)
        
        # Show current winners
        if self.winners:
            print("\n🏆 CURRENT STANDINGS:")
            for rank, racer in self.winners[-5:]:  # Show last 5 finishers
                print(f"  #{rank}: {racer.name}")
    
    def run_race(self) -> None:
        """Run the main race loop."""
        print("\n🎰 Welcome to the Lottery Race! 🎰")
        print("\nAll participants will race to determine the lucky winners!")
        print(f"\nToday's track length: {self.track_length} units")
        print(f"\nTotal contestants: {len(self.contestants)}")
        input("\nPress Enter to start the race...")
        
        self.generate_random_tracks()
        
        # Race loop
        while not all(racer.finished for racer in self.racers):
            self.frame_count += 1
            
            # Move all unfinished racers
            for racer in self.racers:
                if not racer.finished:
                    racer.move()
                    
                    # Record winners as they finish
                    if racer.finished and racer not in [r for _, r in self.winners]:
                        rank = len(self.winners) + 1
                        racer.finish_time = self.frame_count
                        self.winners.append((rank, racer))
            
            # Display current state
            self.display_race()
            
            # Slow down the display for viewing
            time.sleep(0.1)
        
        # Final display
        time.sleep(1)
        self.display_final_results()
    
    def display_final_results(self) -> None:
        """Display the final ranking of all contestants."""
        print("\033[2J\033[H", end='')
        print("=" * 70)
        print(" " * 20 + "🎊 FINAL RESULTS 🎊")
        print("=" * 70)
        print()
        
        print("Congratulations to all participants!\n")
        print("FINAL RANKING:")
        print("-" * 70)
        
        for rank, racer in self.winners:
            medal = ""
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            
            print(f"{medal} #{rank:2d} - {racer.name:15s} (Finished at frame {racer.finish_time})")
        
        print("-" * 70)
        print("\n✨ Thank you for participating in the Lottery Race! ✨")
        print()


def main():
    """Main entry point for the racing lottery game."""
    try:
        game = RacingGame("contestants.csv")
        game.run_race()
    except KeyboardInterrupt:
        print("\n\nRace interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
