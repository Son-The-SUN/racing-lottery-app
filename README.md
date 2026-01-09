# Racing Lottery App 🏁🎰

A Python racing game disguised as a lottery picker! Watch as contestants race to determine the lucky winners.

## Features

- 🏃 **Dynamic Racing**: All contestants race simultaneously with random movements
- 🎲 **Random Track Generation**: Each race has a randomly generated track length
- 👥 **All Participants Visible**: Every contestant appears on screen during the race
- 🏆 **Winner Ranking**: Complete ranking of all participants after the race
- 📊 **CSV Support**: Easy contestant management through CSV files

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Son-The-SUN/racing-lottery-app.git
cd racing-lottery-app
```

2. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Usage

### Quick Start

Run the game with the included sample contestants:

```bash
python racing_lottery.py
```

### Using Your Own Contestants

1. Create or edit `contestants.csv` with your own names:
```csv
Name
Alice
Bob
Charlie
Diana
```

2. Run the game:
```bash
python racing_lottery.py
```

The CSV file should have:
- A header row with "Name" (or any text)
- One name per row in the first column
- At least 2 contestants

## How It Works

1. **Loading**: The game loads contestant names from `contestants.csv`
2. **Track Generation**: A random track length is generated (80-120 units)
3. **Racing**: All contestants race simultaneously with random speed variations
4. **Engagement**: All names are displayed throughout the race
5. **Results**: Final ranking shows all participants in order of finish

## Game Mechanics

- Each racer moves 1-4 units per frame with weighted randomness
- The race continues until all contestants finish
- Real-time display shows each racer's progress
- Winners are recorded as they cross the finish line
- Final results display complete ranking with medals for top 3

## Example Output

```
======================================================================
                    🏁 LOTTERY RACE 🏁
======================================================================

  Alice        [=================>-------------------------------] 34/100
  Bob          [==============>----------------------------------] 28/100
✓ Charlie      [==================================================] 100/100
  Diana        [==================>------------------------------] 36/100

🏆 CURRENT STANDINGS:
  #1: Charlie
======================================================================
```

## Customization

You can customize the game by modifying `racing_lottery.py`:

- Adjust `track_length` range in `RacingGame.__init__()` 
- Change movement speed by modifying weights in `Racer.move()`
- Adjust display refresh rate by changing `time.sleep()` value in `run_race()`
- Customize display symbols and formatting in `display_race()` and `display_final_results()`

## License

This project is open source and available for any use.
