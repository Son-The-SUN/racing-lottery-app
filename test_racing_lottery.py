#!/usr/bin/env python3
"""
Test script for racing lottery game - verifies core functionality
"""
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from racing_lottery import Racer, RacingGame


def test_racer_creation():
    """Test that a racer can be created and initialized properly."""
    racer = Racer("TestName", 100)
    assert racer.name == "TestName"
    assert racer.position == 0
    assert racer.track_length == 100
    assert racer.finished == False
    print("✓ Racer creation test passed")


def test_racer_movement():
    """Test that a racer moves forward."""
    racer = Racer("TestName", 100)
    initial_position = racer.position
    racer.move()
    assert racer.position > initial_position
    assert racer.position <= initial_position + 4  # Max movement per frame
    print("✓ Racer movement test passed")


def test_racer_finish():
    """Test that a racer finishes when reaching the end."""
    racer = Racer("TestName", 10)
    # Move racer until finished
    max_iterations = 100
    iterations = 0
    while not racer.finished and iterations < max_iterations:
        racer.move()
        iterations += 1
    
    assert racer.finished == True
    assert racer.position == 10
    print("✓ Racer finish test passed")


def test_csv_loading():
    """Test that contestants can be loaded from CSV."""
    game = RacingGame("contestants.csv")
    assert len(game.contestants) > 0
    assert "Alice" in game.contestants  # From our sample CSV
    print(f"✓ CSV loading test passed - loaded {len(game.contestants)} contestants")


def test_track_generation():
    """Test that tracks are generated with valid length."""
    game = RacingGame("contestants.csv")
    game.generate_random_tracks()
    assert len(game.racers) == len(game.contestants)
    assert 80 <= game.track_length <= 120
    print(f"✓ Track generation test passed - track length: {game.track_length}")


def test_all_racers_displayed():
    """Test that all contestants become racers."""
    game = RacingGame("contestants.csv")
    game.generate_random_tracks()
    
    racer_names = [racer.name for racer in game.racers]
    
    # Check that all contestants are in racers
    for contestant in game.contestants:
        assert contestant in racer_names
    
    print(f"✓ All racers displayed test passed - {len(racer_names)} racers created")


def test_display_position():
    """Test that display position string is generated correctly."""
    racer = Racer("Test", 100)
    racer.position = 50
    display = racer.get_display_position()
    assert "Test" in display
    assert "[" in display and "]" in display
    assert "50/100" in display
    print("✓ Display position test passed")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running Racing Lottery Game Tests")
    print("=" * 60 + "\n")
    
    try:
        test_racer_creation()
        test_racer_movement()
        test_racer_finish()
        test_csv_loading()
        test_track_generation()
        test_all_racers_displayed()
        test_display_position()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60 + "\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
