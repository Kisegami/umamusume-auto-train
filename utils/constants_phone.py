# Phone screen constants (1080x1920 portrait)
# These are estimated regions for phone screen - you'll need to adjust them manually
# All regions are in PIL format: (left, top, right, bottom)

# Support card icon region (right side of screen)
SUPPORT_CARD_ICON_REGION=(879, 278, 1059, 1169)

# Mood region (top area)
MOOD_REGION=(819, 211, 969, 274)

# Turn region (top left) - more focused to capture just the turn number
TURN_REGION=(21, 149, 210, 239)

# Failure region (bottom area)
FAILURE_REGION=(45, 1357, 1044, 1465)

# Year region (top area)
YEAR_REGION=(21, 66, 276, 96)

# Criteria region (top area)
CRITERIA_REGION=(363, 153, 867, 201)

# Skill points region (bottom right)
SKILL_PTS_REGION=(903, 1383, 1035, 1443) 

# Stat regions for character stats (bottom area)
SPD_REGION=(108, 1284, 204, 1326)
STA_REGION=(273, 1284, 375, 1329)
PWR_REGION=(444, 1284, 543, 1326)
GUTS_REGION=(621, 1281, 711, 1323)
WIT_REGION=(780, 1284, 876, 1323)

# Event detection region (middle area)
EVENT_REGION=(165, 348, 732, 435)

# Race selection regions
RACE_CARD_REGION=(0, 0, 610, 220)  # Dynamic region calculated as (x, y, 350, 110)

# Default screen region (phone resolution)
DEFAULT_SCREEN_REGION=(0, 0, 1080, 1920)

MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]

# Note: All button clicking is done through template matching using button images
# The system finds UI elements dynamically by searching for button images
# No hardcoded positions are needed - this ensures compatibility across different screen sizes 

# Per-type failure rate regions (for direct number OCR)
FAILURE_REGION_SPD = (109, 1404, 205, 1442)
FAILURE_REGION_STA = (308, 1404, 389, 1442)
FAILURE_REGION_PWR = (501, 1404, 579, 1442)
FAILURE_REGION_GUTS = (691, 1404, 769, 1442)
FAILURE_REGION_WIT = (881, 1404, 962, 1442) 