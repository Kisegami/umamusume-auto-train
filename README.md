# Umamusume Auto Training Bot (ADB/Android Version)
[![Discord](https://img.shields.io/badge/Discord-Join%20our%20community-7289DA?style=for-the-badge&logo=discord&logoColor=white)](http://discord.gg/PhVmBtfsKp)

[![GitHub Stars](https://img.shields.io/github/stars/Kisegami/umamusume-auto-train?style=for-the-badge&logo=github)](https://github.com/Kisegami/umamusume-auto-train/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/Kisegami/umamusume-auto-train?style=for-the-badge&logo=github)](https://github.com/Kisegami/umamusume-auto-train/issues)
[![GitHub Forks](https://img.shields.io/github/forks/Kisegami/umamusume-auto-train?style=for-the-badge&logo=github)](https://github.com/Kisegami/umamusume-auto-train/network)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/Kisegami/umamusume-auto-train?style=for-the-badge&logo=github)](https://github.com/Kisegami/umamusume-auto-train/commits)
 

An automated training bot for Umamusume that works with **Android emulators** using ADB (Android Debug Bridge).

**🎮 Platform:** Android Emulator (BlueStacks, LDPlayer, etc.)  
**📱 Resolution:** 1080x1920 (Portrait)  
**🔧 Technology:** ADB commands for screen capture and input

This ADB version provides the same intelligent training logic as the PC version but runs on Android emulators, offering better stability and easier setup.

This project is inspired by [samsulpanjul/umamusume-auto-train](https://github.com/samsulpanjul/umamusume-auto-train)

## Features

### 🤖 ADB/Android Specific Features
- **ADB Integration**: Uses Android Debug Bridge for reliable screen capture and input
- **Emulator Optimized**: Designed specifically for Android emulators (BlueStacks, LDPlayer, etc.)
- **Portrait Layout**: Optimized for 1080x1920 portrait mode gameplay
- **Stable Performance**: More reliable than screen-based automation methods

### 🎯 Training & Racing Intelligence
- Automatically trains Uma with stat prioritization
- Keeps racing until fan count meets the goal, and always picks races with matching aptitude
- Checks mood and handles debuffs automatically
- Rest and recreation management
- Prioritizes G1 races if available for fan farming
- Skill point check for manually skill purchasing
- Stat caps to prevent overtraining specific stats
- Improved training logic with better support card handling
- Minimum support card requirements for training (Read Logic)
- **Intelligent Event Choice Selection**: Automatically analyzes event options and selects the best choice based on configured priorities

## Getting Started

### Requirements

#### Software Requirements
- [Python 3.10+](https://www.python.org/downloads/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for text recognition)
- [ADB (Android Debug Bridge)](https://developer.android.com/studio/command-line/adb) (for Android communication)

#### Android Emulator Requirements
- **Supported Emulators**: The test was done on Mumu Emulator 12, but you might be able to use others
- **Emulator Resolution**: 1080x1920 (Portrait mode)
- **ADB Debugging**: Must be enabled in emulator settings

### Setup

#### 1. Clone Repository

```bash
git clone https://github.com/Kisegami/umamusume-auto-train/
cd umamusume-auto-train
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Tesseract OCR

**Windows:**
1. Download and install from [UB-Mannheim's Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
2. Add Tesseract to your system PATH

#### 4. Setup ADB

1. Download [platform-tools](https://developer.android.com/studio/releases/platform-tools)
2. Extract and add to your system PATH

#### 5. Configure Android Emulator

1. **Install an Android emulator** (BlueStacks recommended)
2. **Set resolution to 1080x1920** (portrait mode)
3. **Enable ADB debugging** in emulator settings
4. **Install Umamusume** in the emulator
5. **Test ADB connection**: `adb devices` (should show your emulator)

#### 6. Configure ADB Settings (Interactive Setup)

Run the interactive ADB setup helper:
```bash
python setup_adb.py
```

This script will:
- ✅ **Detect ADB installation** and available devices
- 🎯 **Auto-configure device connection** (emulator detection)
- ⚙️ **Set optimal timing parameters** (input delay, screenshot timeout)
- 📝 **Update config.json** automatically with ADB settings
- 📱 **Display device info** (model, Android version, screen resolution)

**Manual Configuration Alternative:**
If you prefer manual setup, you can edit the `adb_config` section in your `config.json`:
```json
{
  "adb_config": {
    "device_address": "127.0.0.1:7555",
    "adb_path": "adb",
    "screenshot_timeout": 5,
    "input_delay": 0.5,
    "connection_timeout": 10
  }
}
```

### BEFORE YOU START

Make sure these conditions are met:

#### 🖥️ Emulator Setup
- **Resolution**: Must be 1080x1920 (portrait mode)
- **ADB Connection**: `adb devices` shows your emulator
- **Game Installation**: Umamusume installed and working in emulator

#### 🎮 Game Setup  
- Your Uma must have already won the trophy for each race (the bot will skip the race)
- Turn off all confirmation pop-ups in game settings
- The game must be in the career lobby screen (the one with the Tazuna hint icon)

### Configuration

You can edit your configuration in `config.json`

```json
{
  "priority_stat": ["spd", "sta", "wit", "pwr", "guts"],
  "minimum_mood": "GREAT",
  "maximum_failure": 15,
  "prioritize_g1_race": false,
  "skill_point_cap": 500,
  "enable_skill_point_check": true,
  "min_support": 3,
  "do_race_when_bad_training": true,
  "stat_caps": {
    "spd": 1100,
    "sta": 1100,
    "pwr": 600,
    "guts": 600,
    "wit": 600
  },
  "adb_config": {
    "device_address": "127.0.0.1:7555",
    "adb_path": "adb",
    "screenshot_timeout": 5,
    "input_delay": 0.5,
    "connection_timeout": 10
  },
  "debug_mode": true
}
```

#### Configuration Options

`priority_stat` (array of strings)
- Determines the training stat priority. The bot will focus on these stats in the given order of importance.
- Accepted values: `"spd"`, `"sta"`, `"pwr"`, `"guts"`, `"wit"`

`minimum_mood` (string)
- The lowest acceptable mood the bot will tolerate when deciding to train.
- Accepted values (case-sensitive): `"GREAT"`, `"GOOD"`, `"NORMAL"`, `"BAD"`, `"AWFUL"`
- **Example**: If set to `"NORMAL"`, the bot will train as long as the mood is `"NORMAL"` or better. If the mood drops below that, it'll go for recreation instead.

`maximum_failure` (integer)
- Sets the maximum acceptable failure chance (in percent) before skipping a training option.
- Example: 10 means the bot will avoid training with more than 10% failure risk.

`prioritize_g1_race` (boolean)
- If `true`, the bot will prioritize G1 races except during July and August (summer).
- Useful for fan farming.

`skill_point_cap` (integer) - 
- Maximum skill points before the bot prompts you to spend them.
- The bot will pause on race days and show a prompt if skill points exceed this cap.

`enable_skill_point_check` (boolean) - 
- Enables/disables the skill point cap checking feature.

`min_support` (integer) - 
- Minimum number of support cards required for training (default: 0).
- If no training meet the requirement, the bot will do race instead.
- WIT training requires at least 2 support cards regardless of this setting.
- If you want to turn this off, set it to 0

`do_race_when_bad_training` (boolean) - 
- If `true`, the bot will prioritize racing when no training meets the requirements (insufficient support cards, high failure rates, etc.).
- If `false`, the bot will skip support card requirements and train regardless of `min_support` setting (as long as failure rates are acceptable).
- Default: `true`

`stat_caps` (object) - 
- Maximum values for each stat. The bot will skip training stats that have reached their cap.
- Prevents overtraining and allows focusing on other stats.

`debug_mode` (boolean) - 
- Controls whether debug messages and debug images are saved.
- Set to `false` for normal operation, `true` for troubleshooting.
- When `false`, significantly improves performance by reducing file I/O.

`adb_config` (object) - ADB-specific configuration:
- `device_address` (string) - Target device/emulator address (e.g., "127.0.0.1:7555" for emulator port 7555)
- `adb_path` (string) - Path to ADB executable (usually just "adb" if in PATH)
- `screenshot_timeout` (integer) - Maximum seconds to wait for screenshots (default: 5)
- `input_delay` (float) - Delay between input commands in seconds (default: 0.5)
- `connection_timeout` (integer) - Maximum seconds to wait for ADB connection (default: 10)

Make sure the values match exactly as expected, typos might cause errors.

### Event Choice Configuration

The bot now includes intelligent event choice selection. You can configure which choices are considered "good" or "bad" in `event_priority.json`:

```json
{
  "Good_choices": [
    "Charming",
    "Fast Learner", 
    "Hot Topic",
    "Practice Perfect",
    "Energy +",
    "hint +",
    "Speed +",
    "Stamina +",
    "Yayoi Akikawa bond +",
    "Power +",
    "Wisdom +",
    "Skill points +",
    "Mood +",
    "bond +",
    "stat +",
    "stats +",
    "Guts +",
    "Japanese Oaks"
  ],
  "Bad_choices": [
    "Practice Poor",
    "Slacker",
    "Slow Metabolism", 
    "Mood -",
    "Gatekept"
  ]
}
```

#### Customizing Event Priorities

If you want to customize the event priorities beyond the default configuration, you can reference `all_unique_event_outcomes.json` which contains all possible event outcomes in the game until 08/2025. This file serves as a comprehensive reference for:

- **All possible stat gains** (Speed +10, Stamina +15, etc.)
- **All skill hints** (various skill names with hint bonuses)
- **All support card bond changes** (character names with bond +5/-5)
- **All conditions** (Charming, Hot Topic, Practice Perfect, etc.)
- **All energy changes** (Energy +10, Energy -15, etc.)
- **All mood changes** (Mood +1, Mood -1, etc.)

Use this file to discover new event outcomes you might want to add to your `Good_choices` or `Bad_choices` arrays in `event_priority.json`. For example, if you find a specific skill hint or support card bond change you want to prioritize, you can copy the exact text from `all_unique_event_outcomes.json` and add it to your configuration.

#### Event Choice Selection Logic

The bot automatically selects the best event choice based on your configured priorities:

1. **Priority Analysis**: Chooses options with the highest priority good choices first
2. **Tie-Breaking**: When multiple options have the same good choice:
   - Prefers options with fewer bad choices
   - If still tied, prefers options with more good choices
   - If still tied, defaults to the top choice
3. **Fallback**: For unknown events or analysis failures, defaults to the first choice

#### Event Priority Configuration

`Good_choices` (array of strings)
- List of positive effects that should be prioritized
- The bot will prefer choices containing these terms
- Order matters: earlier items have higher priority

`Bad_choices` (array of strings)
- List of negative effects to avoid
- The bot will prefer choices with fewer of these effects
- Used for tie-breaking when multiple options have the same good choices

### Start

#### 1. Test Your Setup
```bash
# Test ADB connection
adb devices

# Test bot configuration (optional)
python test_adb_setup.py
```
You should see your emulator listed (e.g., `emulator-5554`, `127.0.0.1:5555`)

#### 2. Start the Bot
```bash
python main_adb.py
```

#### 3. Stop the Bot
- Press `Ctrl + C` in your terminal to stop the bot
- Or close the terminal window

> **Note**: Unlike the PC version, this ADB version doesn't use mouse position to stop since it operates through ADB commands.

### Training Logic

The bot uses an improved training logic system:

1. **Junior Year**: Prioritizes training in areas with the most support cards to quickly unlock rainbow training.
2. **Senior/Classic Year**: Prioritizes rainbow training (training with support cards of the same type).
3. **Stat Caps**: Automatically skips training stats that have reached their configured caps.
4. **Support Requirements**: Ensures minimum support card requirements are met before training. If not enough support cards, do race instead.
5. **Fallback Logic**: If rainbow training isn't available, falls back to most support card logic.
6. **Rest Logic**: If energy is too low (every training have high failure rate) => Rest

#### Race Prioritization

When `prioritize_g1_race` is enabled:
- The bot will prioritize racing over training when G1 races are available
- Automatically skips July and August (summer break) for racing
- Checks skill points before race days and prompts if they exceed the cap

### Troubleshooting

#### 🔧 Setup Issues
**ADB Connection Problems:**
```bash
# Re-run the setup script to check configuration
python setup_adb.py

# Test the setup
python test_adb_setup.py

# Manually check ADB
adb devices
adb shell wm size  # Should show 1080x1920
```

**Common Solutions:**
- Restart emulator and run `python setup_adb.py` again
- Check emulator resolution is set to 1080x1920 (portrait)
- Ensure ADB debugging is enabled in emulator settings
- Try different ADB device address if using manual configuration

### Known Issues

#### 🤖 ADB/Android Specific
- Requires stable ADB connection (emulator must stay running)
- May need to restart if emulator restarts or ADB connection is lost
- Performance depends on emulator performance and host system resources

#### 🎮 Game Logic
- Some Uma that has special event/target goals (like Restricted Train Goldship or 2 G1 Race Oguri Cap) may not work. So please avoid using Goldship for training right now to keep your 12 million yen safe. For Oguri Cap, you can turn on Prioritize G1 race
- Tesseract OCR might misread failure chance (e.g., reads 33% as 3%) and proceeds with training anyway
- Sometimes it misdetects debuffs and clicks the infirmary unnecessarily (not a big deal)
- If you bring a friend support card (like Tazuna/Aoi Kiryuin) and do recreation, the bot can't decide whether to date with the friend support card or the Uma
- The bot will skip "3 consecutive races warning" prompt for now
- The bot stuck when "Criteria not met" prompt appears

### TODO

- Add Race Stragety option (right now the only option is manually changing it)
- Do race that doesn't have trophy yet
- Auto-purchase skills (Partially implemented with skill point management)
- Automate Claw Machine event
- Improve Tesseract OCR accuracy for failure chance detection
- Add consecutive races limit
- Add auto retry for failed races
- Add fans tracking/goal for Senior year (Valentine day, Fan Fest and Holiday Season)
- Add option to do race in Summer (July - August)
- ~Add better event options handling~ (✅ **COMPLETED** - Intelligent event choice selection implemented)



### Contribute

If you run into any issues or something doesn't work as expected, feel free to open an issue.
Contributions are also very welcome, I would truly appreciate any support to help improve this project further.
