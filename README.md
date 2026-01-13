# Racing Lottery App 🏁🎰

A visual Pygame-based racing game disguised as a lottery picker! Watch as contestants race down a track with random events, crashes, and boosts to determine the lucky winners.

## Features

- 🏃 **Visual Racing**: A fully graphical racing experience with multiple lanes and a camera system.
- 🎲 **Random Events**: Cars can speed up, slow down, crash, or get super boosts, making the outcome unpredictable.
- 👥 **Massive Participation**: Supports many contestants (loading from CSV).
- 🏆 **Winner Ranking**: Tracks the order of finishers.
- ⚙️ **Configurable**: Adjustable settings via `settings.json`.

## Requirements

- Python 3.6 or higher
- `pygame` library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Son-The-SUN/racing-lottery-app.git
cd racing-lottery-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

Run the game with the included sample contestants:

```bash
python gui_racing_lottery.py
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
python gui_racing_lottery.py
```

## Configuration

You can customize the game settings by editing `settings.json` (if available) or modifying the `gui_racing_lottery.py` file directly. Key settings include:

- **Screen Resolution**: Adjust `screen_width` and `screen_height`.
- **Race/Events**: Configure crash chances and boost probabilities.

## Asset Generation

If assets are missing, you can regenerate default placeholders using:
```bash
python tools/generate_assets.py
```

## License

This project is open source and available for any use.
