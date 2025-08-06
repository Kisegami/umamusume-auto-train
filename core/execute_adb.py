import time
import json
import os
from PIL import ImageStat

from utils.adb_recognizer import locate_on_screen, locate_all_on_screen, wait_for_image, is_image_on_screen, match_template
from utils.adb_input import tap, click_at_coordinates, triple_click, move_to_and_click, mouse_down, mouse_up, scroll_down, scroll_up
from utils.adb_screenshot import take_screenshot, enhanced_screenshot, capture_region
from utils.constants_phone import (
    MOOD_LIST, EVENT_REGION, RACE_CARD_REGION
)

# Import ADB state and logic modules
from core.state_adb import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria, check_skill_points_cap
from core.logic import do_something, do_something_fallback, all_training_unsafe, MAX_FAILURE

# Load config and check debug mode
with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    DEBUG_MODE = config.get("debug_mode", False)

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print(message)

def is_infirmary_active_adb(button_location):
    """
    Check if the infirmary button is active (bright) or disabled (dark).
    Args:
        button_location: tuple (x, y, w, h) of the button location
    Returns:
        bool: True if button is active (bright), False if disabled (dark)
    """
    try:
        x, y, w, h = button_location
        
        # Take screenshot and crop the button region
        screenshot = take_screenshot()
        button_region = screenshot.crop((x, y, x + w, y + h))
        
        # Convert to grayscale and calculate average brightness
        grayscale = button_region.convert("L")
        stat = ImageStat.Stat(grayscale)
        avg_brightness = stat.mean[0]
        
        # Threshold for active button (same as PC version)
        is_active = avg_brightness > 150
        debug_print(f"[DEBUG] Infirmary brightness: {avg_brightness:.1f} ({'active' if is_active else 'disabled'})")
        
        return is_active
    except Exception as e:
        print(f"[ERROR] Failed to check infirmary button brightness: {e}")
        return False


def count_event_choices():
    """
    Count how many event choice icons are found on screen.
    Uses event_choice_1.png as template to find all U-shaped icons.
    Returns:
        tuple: (count, locations) - number of unique choices found and their locations
    """
    template_path = "assets/icons/event_choice_1.png"
    
    if not os.path.exists(template_path):
        debug_print(f"[DEBUG] Template not found: {template_path}")
        return 0, []
    
    try:
        debug_print(f"[DEBUG] Searching for event choices using: {template_path}")
        # Search for all instances of the template in the event choice region
        event_choice_region = (6, 450, 126, 1776)
        locations = locate_all_on_screen(template_path, confidence=0.45, region=event_choice_region)
        debug_print(f"[DEBUG] Raw locations found: {len(locations)}")
        if not locations:
            debug_print("[DEBUG] No event choice locations found")
            return 0, []
        # Sort locations by y, then x (top to bottom, left to right)
        locations = sorted(locations, key=lambda loc: (loc[1], loc[0]))
        unique_locations = []
        for i, location in enumerate(locations):
            x, y, w, h = location
            center = (x + w//2, y + h//2)
            if not unique_locations:
                unique_locations.append(location)
                continue
            # Only compare to the last accepted unique match
            last_x, last_y, last_w, last_h = unique_locations[-1]
            last_center = (last_x + last_w//2, last_y + last_h//2)
            distance = ((center[0] - last_center[0]) ** 2 + (center[1] - last_center[1]) ** 2) ** 0.5
            if distance >= 150:  # Increased from 30 to 150 to separate different choice rows
                unique_locations.append(location)
        debug_print(f"[DEBUG] Final unique locations: {len(unique_locations)}")
        return len(unique_locations), unique_locations
    except Exception as e:
        print(f"❌ Error counting event choices: {str(e)}")
        return 0, []

def load_event_priorities():
    """Load event priority configuration from event_priority.json"""
    try:
        if os.path.exists("event_priority.json"):
            with open("event_priority.json", "r", encoding="utf-8") as f:
                priorities = json.load(f)
            return priorities
        else:
            print("Warning: event_priority.json not found")
            return {"Good_choices": [], "Bad_choices": []}
    except Exception as e:
        print(f"Error loading event priorities: {e}")
        return {"Good_choices": [], "Bad_choices": []}

def analyze_event_options(options, priorities):
    """
    Analyze event options and recommend the best choice based on priorities.
    
    Args:
        options: Dict of option_name -> option_reward
        priorities: Dict with "Good_choices" and "Bad_choices" lists
    
    Returns:
        Dict with recommendation info:
        {
            "recommended_option": str,
            "recommendation_reason": str,
            "option_analysis": dict,
            "all_options_bad": bool
        }
    """
    good_choices = priorities.get("Good_choices", [])
    bad_choices = priorities.get("Bad_choices", [])
    
    option_analysis = {}
    all_options_bad = True
    
    # Analyze each option
    for option_name, option_reward in options.items():
        reward_lower = option_reward.lower()
        
        # Check for good choices
        good_matches = []
        for good_choice in good_choices:
            if good_choice.lower() in reward_lower:
                good_matches.append(good_choice)
        
        # Check for bad choices
        bad_matches = []
        for bad_choice in bad_choices:
            if bad_choice.lower() in reward_lower:
                bad_matches.append(bad_choice)
        
        option_analysis[option_name] = {
            "reward": option_reward,
            "good_matches": good_matches,
            "bad_matches": bad_matches,
            "has_good": len(good_matches) > 0,
            "has_bad": len(bad_matches) > 0
        }
        
        # If any option has good choices, not all options are bad
        if len(good_matches) > 0:
            all_options_bad = False
    
    # Check if ALL options have bad choices (regardless of good choices)
    all_options_have_bad = all(analysis["has_bad"] for analysis in option_analysis.values())
    
    # Determine recommendation
    recommended_option = None
    recommendation_reason = ""
    
    if all_options_have_bad:
        # If all options have bad choices, ignore bad choices and pick based on good choice priority
        best_options = []  # Store all options with the same best priority
        best_priority = -1
        
        for option_name, analysis in option_analysis.items():
            # Find the highest priority good choice in this option
            for good_choice in analysis["good_matches"]:
                try:
                    priority = good_choices.index(good_choice)
                    if priority < best_priority or best_priority == -1:
                        # New best priority found, reset the list
                        best_priority = priority
                        best_options = [option_name]
                    elif priority == best_priority:
                        # Same priority, add to the list
                        if option_name not in best_options:
                            best_options.append(option_name)
                except ValueError:
                    continue
        
        if best_options:
            # If we have multiple options with the same priority, use tie-breaking
            if len(best_options) > 1:
                # Since all options have bad choices, ignore bad choices and prefer option with more good choices
                best_option = None
                max_good_choices = -1
                
                for option_name in best_options:
                    good_count = len(option_analysis[option_name]["good_matches"])
                    if good_count > max_good_choices:
                        max_good_choices = good_count
                        best_option = option_name
                
                # If still tied, choose the first option (top choice)
                if best_option is None:
                    best_option = best_options[0]
                
                recommended_option = best_option
                recommendation_reason = f"All options have bad choices. Multiple options have same priority good choice. Selected based on tie-breaking (more good choices, then top choice)."
            else:
                best_option = best_options[0]
                recommended_option = best_option
                recommendation_reason = f"All options have bad choices. Recommended based on highest priority good choice: '{option_analysis[best_option]['good_matches'][0]}'"
        else:
            # No good choices found, pick the option with the least bad choices
            best_option = None
            min_bad_choices = 999
            
            for option_name, analysis in option_analysis.items():
                bad_count = len(analysis["bad_matches"])
                if bad_count < min_bad_choices:
                    min_bad_choices = bad_count
                    best_option = option_name
            
            if best_option:
                recommended_option = best_option
                recommendation_reason = f"All options have bad choices. Selected option with least bad choices: {len(option_analysis[best_option]['bad_matches'])} bad choices"
            else:
                recommendation_reason = "All options have bad choices. No recommendation possible."
    else:
        # Normal case: some options don't have bad choices - avoid bad choices completely
        best_options = []
        best_priority = -1
        
        for option_name, analysis in option_analysis.items():
            # ONLY consider options that have good choices AND NO bad choices
            if analysis["has_good"] and not analysis["has_bad"]:
                # Find the highest priority good choice in this option
                for good_choice in analysis["good_matches"]:
                    try:
                        priority = good_choices.index(good_choice)
                        if priority < best_priority or best_priority == -1:
                            # New best priority found, reset the list
                            best_priority = priority
                            best_options = [option_name]
                        elif priority == best_priority:
                            # Same priority, add to the list
                            if option_name not in best_options:
                                best_options.append(option_name)
                    except ValueError:
                        continue
        
        if best_options:
            # If we have multiple options with the same priority, use tie-breaking
            if len(best_options) > 1:
                # Prefer option with more good choices, then fewer bad choices
                best_option = None
                max_good_choices = -1
                min_bad_choices = 999
                
                for option_name in best_options:
                    good_count = len(option_analysis[option_name]["good_matches"])
                    bad_count = len(option_analysis[option_name]["bad_matches"])
                    
                    if good_count > max_good_choices or (good_count == max_good_choices and bad_count < min_bad_choices):
                        max_good_choices = good_count
                        min_bad_choices = bad_count
                        best_option = option_name
                
                recommended_option = best_option
                recommendation_reason = f"Multiple options have same priority good choice. Selected based on tie-breaking (more good choices, then fewer bad choices)."
            else:
                best_option = best_options[0]
                recommended_option = best_option
                recommendation_reason = f"Recommended based on highest priority good choice: '{option_analysis[best_option]['good_matches'][0]}'"
        else:
            # No clean options (good without bad) found, try options with good choices even if they have bad choices
            debug_print("[DEBUG] No clean options found, considering options with good choices despite bad choices...")
            fallback_options = []
            best_priority = -1
            
            for option_name, analysis in option_analysis.items():
                if analysis["has_good"]:  # Has good choices (ignoring bad choices for now)
                    # Find the highest priority good choice in this option
                    for good_choice in analysis["good_matches"]:
                        try:
                            priority = good_choices.index(good_choice)
                            if priority < best_priority or best_priority == -1:
                                # New best priority found, reset the list
                                best_priority = priority
                                fallback_options = [option_name]
                            elif priority == best_priority:
                                # Same priority, add to the list
                                if option_name not in fallback_options:
                                    fallback_options.append(option_name)
                        except ValueError:
                            continue
            
            if fallback_options:
                # Choose from fallback options, prefer fewer bad choices
                best_option = None
                min_bad_choices = 999
                
                for option_name in fallback_options:
                    bad_count = len(option_analysis[option_name]["bad_matches"])
                    if bad_count < min_bad_choices:
                        min_bad_choices = bad_count
                        best_option = option_name
                
                recommended_option = best_option
                recommendation_reason = f"No clean options available. Selected option with good choices but fewest bad choices: {min_bad_choices} bad choices"
            else:
                # Absolutely no good choices found, pick the option with the least bad choices
                best_option = None
                min_bad_choices = 999
                
                for option_name, analysis in option_analysis.items():
                    bad_count = len(analysis["bad_matches"])
                    if bad_count < min_bad_choices:
                        min_bad_choices = bad_count
                        best_option = option_name
                
                if best_option:
                    recommended_option = best_option
                    recommendation_reason = f"No good choices found. Selected option with least bad choices: {len(option_analysis[best_option]['bad_matches'])} bad choices"
                else:
                    recommendation_reason = "No good choices found. No recommendation possible."
    
    return {
        "recommended_option": recommended_option,
        "recommendation_reason": recommendation_reason,
        "option_analysis": option_analysis,
        "all_options_bad": all_options_bad
    }

def generate_event_variations(event_name):
    """
    Generate variations of an event name for better matching.
    
    Args:
        event_name: The base event name
    
    Returns:
        List of event name variations
    """
    variations = [event_name]
    
    # Add common variations
    if " " in event_name:
        # Split by spaces and create combinations
        parts = event_name.split()
        variations.extend(parts)
        
        # Add combinations of parts
        for i in range(len(parts)):
            for j in range(i + 1, len(parts) + 1):
                combination = " ".join(parts[i:j])
                if combination not in variations:
                    variations.append(combination)
    
    # Add lowercase versions
    variations.append(event_name.lower())
    
    # Add versions without special characters
    clean_name = event_name.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    if clean_name not in variations:
        variations.append(clean_name)
    
    return variations

def search_events(event_variations):
    """Search for matching events in databases (same as original PC version)"""
    found_events = {}
    
    # Load support card events
    support_events = []
    if os.path.exists("assets/events/support_card.json"):
        with open("assets/events/support_card.json", "r", encoding="utf-8-sig") as f:
            support_events = json.load(f)
    
    # Load uma data events
    uma_events = []
    if os.path.exists("assets/events/uma_data.json"):
        with open("assets/events/uma_data.json", "r", encoding="utf-8-sig") as f:
            uma_data = json.load(f)
            # Extract all UmaEvents from all characters
            for character in uma_data:
                if "UmaEvents" in character:
                    uma_events.extend(character["UmaEvents"])
    
    # Load ura finale events
    ura_events = []
    if os.path.exists("assets/events/ura_finale.json"):
        with open("assets/events/ura_finale.json", "r", encoding="utf-8-sig") as f:
            ura_events = json.load(f)
    
    # Search in support card events
    for event in support_events:
        db_event_name = event.get("EventName", "").lower()
        # Remove chain event symbols and extra spaces for comparison
        clean_db_name = db_event_name.replace("(❯)", "").replace("(❯❯)", "").replace("(❯❯❯)", "").strip()
        
        # Try matching with all variations
        for variation in event_variations:
            clean_search_name = variation.lower().strip()
            
            if clean_db_name == clean_search_name:
                event_name_key = event['EventName']
                if event_name_key not in found_events:
                    found_events[event_name_key] = {"source": "Support Card", "options": {}}
                
                # Filter and add valid options
                event_options = event.get("EventOptions", {})
                for option_name, option_reward in event_options.items():
                    # Only include standard option names
                    if option_name and any(keyword in option_name.lower() for keyword in 
                                         ["top option", "bottom option", "middle option", "option1", "option2", "option3"]):
                        found_events[event_name_key]["options"][option_name] = option_reward
                break  # Found a match, no need to try other variations
    
    # Search in uma events
    for event in uma_events:
        db_event_name = event.get("EventName", "").lower()
        # Remove chain event symbols and extra spaces for comparison
        clean_db_name = db_event_name.replace("(❯)", "").replace("(❯❯)", "").replace("(❯❯❯)", "").strip()
        
        # Try matching with all variations
        for variation in event_variations:
            clean_search_name = variation.lower().strip()
            
            if clean_db_name == clean_search_name:
                event_name_key = event['EventName']
                if event_name_key not in found_events:
                    found_events[event_name_key] = {"source": "Uma Data", "options": {}}
                elif found_events[event_name_key]["source"] == "Support Card":
                    found_events[event_name_key]["source"] = "Both"
                
                # Filter and add valid options
                event_options = event.get("EventOptions", {})
                for option_name, option_reward in event_options.items():
                    # Only include standard option names
                    if option_name and any(keyword in option_name.lower() for keyword in 
                                         ["top option", "bottom option", "middle option", "option1", "option2", "option3"]):
                        found_events[event_name_key]["options"][option_name] = option_reward
                break  # Found a match, no need to try other variations
    
    # Search in ura finale events
    for event in ura_events:
        db_event_name = event.get("EventName", "").lower()
        # Remove chain event symbols and extra spaces for comparison
        clean_db_name = db_event_name.replace("(❯)", "").replace("(❯❯)", "").replace("(❯❯❯)", "").strip()
        
        # Try matching with all variations
        for variation in event_variations:
            clean_search_name = variation.lower().strip()
            
            if clean_db_name == clean_search_name:
                event_name_key = event['EventName']
                if event_name_key not in found_events:
                    found_events[event_name_key] = {"source": "Ura Finale", "options": {}}
                elif found_events[event_name_key]["source"] == "Support Card":
                    found_events[event_name_key]["source"] = "Support Card + Ura Finale"
                elif found_events[event_name_key]["source"] == "Uma Data":
                    found_events[event_name_key]["source"] = "Uma Data + Ura Finale"
                elif found_events[event_name_key]["source"] == "Both":
                    found_events[event_name_key]["source"] = "All Sources"
                
                # Filter and add valid options
                event_options = event.get("EventOptions", {})
                for option_name, option_reward in event_options.items():
                    # Only include standard option names
                    if option_name and any(keyword in option_name.lower() for keyword in 
                                         ["top option", "bottom option", "middle option", "option1", "option2", "option3"]):
                        found_events[event_name_key]["options"][option_name] = option_reward
                break  # Found a match, no need to try other variations
    
    return found_events

def handle_event_choice():
    """
    Main function to handle event detection and choice selection.
    This function should be called when an event is detected.
    
    Returns:
        tuple: (choice_number, success, choice_locations) - choice number, success status, and found locations
    """
    # Define the region for event name detection
    event_region = EVENT_REGION
    
    print("Event detected, scan event")
    
    try:
        # Wait for event to stabilize (1 second)
        time.sleep(1.0)
        
        # Capture the event name
        from utils.adb_screenshot import capture_region
        from core.ocr import extract_event_name_text
        event_image = capture_region(event_region)
        event_name = extract_event_name_text(event_image)
        event_name = event_name.strip()
        
        if not event_name:
            print("No text detected in event region")
            return 1, False, []  # Default to first choice
        
        print(f"Event found: {event_name}")
        
        # Generate variations for better matching
        event_variations = generate_event_variations(event_name)
        
        # Search for matching events
        found_events = search_events(event_variations)
        
        # Count event choices on screen
        choices_found, choice_locations = count_event_choices()
        
        # Load event priorities
        priorities = load_event_priorities()
        
        if found_events:
            # Event found in database
            event_name_key = list(found_events.keys())[0]
            event_data = found_events[event_name_key]
            options = event_data["options"]
            
            print(f"Source: {event_data['source']}")
            print("Options:")
            
            if options:
                # Analyze options with priorities
                analysis = analyze_event_options(options, priorities)
                
                for option_name, option_reward in options.items():
                    # Replace all line breaks with ', '
                    reward_single_line = option_reward.replace("\r\n", ", ").replace("\n", ", ").replace("\r", ", ")
                    
                    # Add analysis indicators
                    option_analysis = analysis["option_analysis"][option_name]
                    indicators = []
                    if option_analysis["has_good"]:
                        indicators.append("✅ Good")
                    if option_analysis["has_bad"]:
                        indicators.append("❌ Bad")
                    if option_name == analysis["recommended_option"]:
                        indicators.append("🎯 RECOMMENDED")
                    
                    indicator_text = f" [{', '.join(indicators)}]" if indicators else ""
                    print(f"  {option_name}: {reward_single_line}{indicator_text}")
                
                # Print recommendation
                print(f"Recommend: {analysis['recommended_option']}")
                
                # Determine which choice to select based on recommendation and choice count
                expected_options = len(options)
                recommended_option = analysis["recommended_option"]
                
                # If no recommendation, default to first choice
                if recommended_option is None:
                    print("No recommendation found, defaulting to first choice")
                    choice_number = 1
                else:
                    # Map recommended option to choice number
                    choice_number = 1  # Default to first choice
                    
                    if expected_options == 2:
                        if "top" in recommended_option.lower():
                            choice_number = 1
                        elif "bottom" in recommended_option.lower():
                            choice_number = 2
                    elif expected_options == 3:
                        if "top" in recommended_option.lower():
                            choice_number = 1
                        elif "middle" in recommended_option.lower():
                            choice_number = 2
                        elif "bottom" in recommended_option.lower():
                            choice_number = 3
                    elif expected_options >= 4:
                        # For 4+ choices, look for "Option 1", "Option 2", etc.
                        import re
                        option_match = re.search(r'option\s*(\d+)', recommended_option.lower())
                        if option_match:
                            choice_number = int(option_match.group(1))
                
                # Verify choice number is valid
                if choice_number > choices_found:
                    print(f"Warning: Recommended choice {choice_number} exceeds available choices ({choices_found})")
                    choice_number = 1  # Fallback to first choice
                
                print(f"Choose choice: {choice_number}")
                return choice_number, True, choice_locations
            else:
                print("No valid options found in database")
                return 1, False, choice_locations
        else:
            # Unknown event
            print("Unknown event - not found in database")
            print(f"Choices found: {choices_found}")
            return 1, False, choice_locations  # Default to first choice for unknown events
    
    except Exception as e:
        print(f"Error during event handling: {e}")
        return 1, False, []  # Default to first choice on error

def click_event_choice(choice_number, choice_locations=None):
    """
    Click on the specified event choice using pre-found locations.
    
    Args:
        choice_number: The choice number to click (1, 2, 3, etc.)
        choice_locations: Pre-found locations from count_event_choices() (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use pre-found locations if provided, otherwise search again
        if choice_locations is None:
            debug_print("[DEBUG] No pre-found locations, searching for event choices...")
            event_choice_region = (6, 450, 126, 1776)
            choice_locations = locate_all_on_screen("assets/icons/event_choice_1.png", confidence=0.45, region=event_choice_region)
            
            if not choice_locations:
                print("No event choice icons found")
                return False
            
            # Filter out duplicates
            unique_locations = []
            for location in choice_locations:
                x, y, w, h = location
                center = (x + w//2, y + h//2)
                is_duplicate = False
                
                for existing in unique_locations:
                    ex, ey, ew, eh = existing
                    existing_center = (ex + ew//2, ey + eh//2)
                    distance = ((center[0] - existing_center[0]) ** 2 + (center[1] - existing_center[1]) ** 2) ** 0.5
                    if distance < 30:  # Within 30 pixels
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_locations.append(location)
            
            # Sort locations by Y coordinate (top to bottom)
            unique_locations.sort(key=lambda loc: loc[1])
        else:
            debug_print("[DEBUG] Using pre-found choice locations")
            unique_locations = choice_locations
        
        # Click the specified choice
        if 1 <= choice_number <= len(unique_locations):
            target_location = unique_locations[choice_number - 1]
            x, y, w, h = target_location
            center = (x + w//2, y + h//2)
            
            print(f"Clicking choice {choice_number} at position {center}")
            tap(center[0], center[1])
            return True
        else:
            print(f"Invalid choice number: {choice_number} (available: 1-{len(unique_locations)})")
            return False
    
    except Exception as e:
        print(f"Error clicking event choice: {e}")
        return False

def is_racing_available(year):
    """Check if racing is available based on the current year/month"""
    # No races in Pre-Debut
    if "Pre-Debut" in year:
        return False
    year_parts = year.split(" ")
    # No races in July and August (summer break)
    if len(year_parts) > 3 and year_parts[3] in ["Jul", "Aug"]:
        return False
    return True

def click(img, confidence=0.8, minSearch=1, click=1, text="", region=None):
    """Click on image with retry logic"""
    debug_print(f"[DEBUG] Looking for: {img}")
    for attempt in range(int(minSearch)):
        btn = locate_on_screen(img, confidence=confidence, region=region)
        if btn:
            if text:
                print(text)
            debug_print(f"[DEBUG] Clicking {img} at position {btn}")
            tap(btn[0], btn[1])
            return True
        if attempt < int(minSearch) - 1:  # Don't sleep on last attempt
            debug_print(f"[DEBUG] Attempt {attempt + 1}: {img} not found")
            time.sleep(0.05)  # Reduced from 0.1 to 0.05
    debug_print(f"[DEBUG] Failed to find {img} after {minSearch} attempts")
    return False

def go_to_training():
    """Go to training screen"""
    debug_print("[DEBUG] Going to training screen...")
    return click("assets/buttons/training_btn.png")

def check_training():
    """Check training results with support cards and failure rates using fixed coordinates"""
    debug_print("[DEBUG] Checking training options...")
    
    # Fixed coordinates for each training type
    training_coords = {
        "spd": (165, 1557),
        "sta": (357, 1563),
        "pwr": (546, 1557),
        "guts": (735, 1566),
        "wit": (936, 1572)
    }
    results = {}

    for key, coords in training_coords.items():
        debug_print(f"[DEBUG] Checking {key.upper()} training at coordinates {coords}...")
        
        # Proper hover simulation: move to position, hold, check, move away, release
        debug_print(f"[DEBUG] Hovering over {key.upper()} training to check support cards...")
        
        # Step 1: Hold at button position and move mouse up 300 pixels to simulate hover
        debug_print(f"[DEBUG] Holding at {key.upper()} training button and moving mouse up...")
        from utils.adb_input import swipe
        # Swipe from button position up 300 pixels with longer duration to simulate holding and moving
        start_x, start_y = coords
        end_x, end_y = start_x, start_y - 300  # Move up 300 pixels
        swipe(start_x, start_y, end_x, end_y, duration_ms=200)  # Longer duration for hover effect
        time.sleep(0.3)  # Wait for hover effect to register
        
        # Step 2: Check support cards while hovering
        support_counts = check_support_card()
        total_support = sum(support_counts.values())
        debug_print(f"[DEBUG] Support cards detected: {support_counts} (total: {total_support})")
        

        
        debug_print(f"[DEBUG] Checking failure rate for {key.upper()} training...")
        failure_chance, confidence = check_failure(key)
        
        results[key] = {
            "support": support_counts,
            "total_support": total_support,
            "failure": failure_chance,
            "confidence": confidence
        }
        
        print(f"[{key.upper()}] → {support_counts}, Fail: {failure_chance}% - Confident: {confidence:.2f}")
        

    
    debug_print("[DEBUG] Going back from training screen...")
    click("assets/buttons/back_btn.png")
    return results

def do_train(train):
    """Perform training of specified type"""
    debug_print(f"[DEBUG] Performing {train.upper()} training...")
    
    # First, go to training screen
    if not go_to_training():
        debug_print(f"[DEBUG] Failed to go to training screen, cannot perform {train.upper()} training")
        return
    
    # Wait for screen to load and verify we're on training screen
    time.sleep(1.0)
    
    # Fixed coordinates for each training type
    training_coords = {
        "spd": (165, 1557),
        "sta": (357, 1563),
        "pwr": (546, 1557),
        "guts": (735, 1566),
        "wit": (936, 1572)
    }
    
    # Check if the requested training type exists
    if train not in training_coords:
        debug_print(f"[DEBUG] Unknown training type: {train}")
        return
    
    # Get the coordinates for the requested training type
    train_coords = training_coords[train]
    debug_print(f"[DEBUG] Found {train.upper()} training at coordinates {train_coords}")
    triple_click(train_coords[0], train_coords[1], interval=0.1)
    debug_print(f"[DEBUG] Triple clicked {train.upper()} training button")

def do_rest():
    """Perform rest action"""
    debug_print("[DEBUG] Performing rest action...")
    rest_btn = locate_on_screen("assets/buttons/rest_btn.png", confidence=0.8)
    rest_summer_btn = locate_on_screen("assets/buttons/rest_summer_btn.png", confidence=0.8)
    
    if rest_btn:
        debug_print(f"[DEBUG] Found rest button at {rest_btn}")
        tap(rest_btn[0], rest_btn[1])
        debug_print("[DEBUG] Clicked rest button")
    elif rest_summer_btn:
        debug_print(f"[DEBUG] Found summer rest button at {rest_summer_btn}")
        tap(rest_summer_btn[0], rest_summer_btn[1])
        debug_print("[DEBUG] Clicked summer rest button")
    else:
        debug_print("[DEBUG] No rest button found")

def do_recreation():
    """Perform recreation action"""
    debug_print("[DEBUG] Performing recreation action...")
    recreation_btn = locate_on_screen("assets/buttons/recreation_btn.png", confidence=0.8)
    recreation_summer_btn = locate_on_screen("assets/buttons/rest_summer_btn.png", confidence=0.8)
    
    if recreation_btn:
        debug_print(f"[DEBUG] Found recreation button at {recreation_btn}")
        tap(recreation_btn[0], recreation_btn[1])
        debug_print("[DEBUG] Clicked recreation button")
    elif recreation_summer_btn:
        debug_print(f"[DEBUG] Found summer recreation button at {recreation_summer_btn}")
        tap(recreation_summer_btn[0], recreation_summer_btn[1])
        debug_print("[DEBUG] Clicked summer recreation button")
    else:
        debug_print("[DEBUG] No recreation button found")

def do_race(prioritize_g1=False):
    """Perform race action"""
    debug_print(f"[DEBUG] Performing race action (G1 priority: {prioritize_g1})...")
    click("assets/buttons/races_btn.png", minSearch=10)
    time.sleep(1.2)
    click("assets/buttons/ok_btn.png", minSearch=1)

    found = race_select(prioritize_g1=prioritize_g1)
    if found:
        debug_print("[DEBUG] Race found and selected, proceeding to race preparation")
        race_prep()
        time.sleep(1)
        after_race()
        return True
    else:
        debug_print("[DEBUG] No race found, going back")
        click("assets/buttons/back_btn.png", minSearch=0.7)
        return False

def race_day():
    """Handle race day"""
    # Check skill points cap before race day (if enabled)
    import json
    
    # Load config to check if skill point check is enabled
    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)
    
    enable_skill_check = config.get("enable_skill_point_check", True)
    
    if enable_skill_check:
        print("[INFO] Race Day - Checking skill points cap...")
        check_skill_points_cap()
    
    debug_print("[DEBUG] Clicking race day button...")
    if click("assets/buttons/race_day_btn.png", minSearch=10):
        debug_print("[DEBUG] Race day button clicked, clicking OK button...")
        time.sleep(1.3)
        click("assets/buttons/ok_btn.png", minSearch=1)
        time.sleep(0.5)
        
        debug_print("[DEBUG] Selecting race using match_track.png...")
        # Use race_select to find and select the right race using match_track.png
        found = race_select(prioritize_g1=False)  # Race day doesn't prioritize G1
        if not found:
            print("[INFO] No suitable race found on race day.")
            return False
        
        debug_print("[DEBUG] Starting race preparation...")
        race_prep()
        time.sleep(1)
        after_race()
        return True
    return False

def race_select(prioritize_g1=False):
    """Select race"""
    debug_print(f"[DEBUG] Selecting race (G1 priority: {prioritize_g1})...")
    
    # # Move to center position like PC version
    # from utils.adb_input import tap
    # tap(560, 680)  # Center position like PC version
    # time.sleep(0.2)
    
    def find_and_select_race():
        """Helper function to find and select a race (G1 or normal)"""
        # Wait for race list to load before detection
        debug_print("[DEBUG] Waiting for race list to load...")
        time.sleep(1.5)
        
        # Check initial screen first
        if prioritize_g1:
            debug_print("[DEBUG] Looking for G1 race.")
            screenshot = take_screenshot()
            race_cards = match_template(screenshot, "assets/ui/g1_race.png", confidence=0.9)
            debug_print(f"[DEBUG] Initial G1 detection result: {race_cards}")
            
            if race_cards:
                debug_print(f"[DEBUG] Found {len(race_cards)} G1 race card(s), searching for match_track within regions...")
                for x, y, w, h in race_cards:
                    # Search for match_track.png within the race card region
                    region = (x, y, RACE_CARD_REGION[2], RACE_CARD_REGION[3])
                    debug_print(f"[DEBUG] Searching region: {region}")
                    match_aptitude = locate_on_screen("assets/ui/match_track.png", confidence=0.6, region=region)
                    if match_aptitude:
                        debug_print(f"[DEBUG] ✅ Match track found at {match_aptitude} in region {region}")
                    else:
                        debug_print(f"[DEBUG] ❌ No match track found in region {region}")
                    if match_aptitude:
                        debug_print(f"[DEBUG] G1 race found at {match_aptitude}")
                        tap(match_aptitude[0], match_aptitude[1])
                        time.sleep(0.2)
                        
                        # Click race button twice like PC version
                        for j in range(2):
                            race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.6)
                            if race_btn:
                                debug_print(f"[DEBUG] Found race button at {race_btn}")
                                tap(race_btn[0], race_btn[1])
                                time.sleep(0.5)
                            else:
                                debug_print("[DEBUG] Race button not found")
                        return True
            else:
                debug_print("[DEBUG] No G1 race cards found on initial screen, will try swiping...")
        else:
            debug_print("[DEBUG] Looking for race.")
            match_aptitude = locate_on_screen("assets/ui/match_track.png", confidence=0.6)
            if match_aptitude:
                debug_print(f"[DEBUG] Race found at {match_aptitude}")
                tap(match_aptitude[0], match_aptitude[1])
                time.sleep(0.2)
                
                # Click race button twice like PC version
                for j in range(2):
                    race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.8)
                    if race_btn:
                        debug_print(f"[DEBUG] Found race button at {race_btn}")
                        tap(race_btn[0], race_btn[1])
                        time.sleep(0.5)
                    else:
                        debug_print("[DEBUG] Race button not found")
                return True
        
        # If not found on initial screen, try scrolling up to 4 times
        for scroll in range(4):
            # Use direct swipe instead of scroll_down
            from utils.adb_input import swipe
            debug_print(f"[DEBUG] Swiping from (378,1425) to (378,1106) (attempt {scroll+1}/4)")
            swipe(378, 1425, 378, 1106, duration_ms=500)
            time.sleep(0.2)
            
            # Check for race again after each swipe
            if prioritize_g1:
                screenshot = take_screenshot()
                race_cards = match_template(screenshot, "assets/ui/g1_race.png", confidence=0.9)
                
                if race_cards:
                    debug_print(f"[DEBUG] Found {len(race_cards)} G1 race card(s) after swipe {scroll+1}")
                    for i, (x, y, w, h) in enumerate(race_cards):
                        debug_print(f"[DEBUG] G1 Race Card {i+1}: bbox=({x}, {y}, {w}, {h})")
                        # Search for match_track.png within the race card region
                        region = (x, y, RACE_CARD_REGION[2], RACE_CARD_REGION[3])
                        debug_print(f"[DEBUG] Extended region: {region}")
                        match_aptitude = locate_on_screen("assets/ui/match_track.png", confidence=0.6, region=region)
                        if match_aptitude:
                            debug_print(f"[DEBUG] ✅ Match track found at {match_aptitude} in region {region}")
                        else:
                            debug_print(f"[DEBUG] ❌ No match track found in region {region}")
                        if match_aptitude:
                            debug_print(f"[DEBUG] G1 race found at {match_aptitude} after swipe {scroll+1}")
                            tap(match_aptitude[0], match_aptitude[1])
                            time.sleep(0.2)
                            
                            # Click race button twice like PC version
                            for j in range(2):
                                race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.8)
                                if race_btn:
                                    debug_print(f"[DEBUG] Found race button at {race_btn}")
                                    tap(race_btn[0], race_btn[1])
                                    time.sleep(0.5)
                                else:
                                    debug_print("[DEBUG] Race button not found")
                            return True
                else:
                    debug_print(f"[DEBUG] No G1 race cards found after swipe {scroll+1}")
            else:
                debug_print(f"[DEBUG] Looking for any race (non-G1) after swipe {scroll+1}")
                match_aptitude = locate_on_screen("assets/ui/match_track.png", confidence=0.6)
                if match_aptitude:
                    debug_print(f"[DEBUG] Race found at {match_aptitude} after swipe {scroll+1}")
                    tap(match_aptitude[0], match_aptitude[1])
                    time.sleep(0.2)
                    
                    # Click race button twice like PC version
                    for j in range(2):
                        race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.8)
                        if race_btn:
                            debug_print(f"[DEBUG] Found race button at {race_btn}")
                            tap(race_btn[0], race_btn[1])
                            time.sleep(0.5)
                        else:
                            debug_print("[DEBUG] Race button not found")
                    return True
                else:
                    debug_print(f"[DEBUG] No races found after swipe {scroll+1}")
        
        return False
    
    # Use the unified race finding logic
    found = find_and_select_race()
    if not found:
        debug_print("[DEBUG] No suitable race found")
    return found

def race_prep():
    """Prepare for race"""
    debug_print("[DEBUG] Preparing for race...")
    view_result_btn = wait_for_image("assets/buttons/view_results.png", timeout=20)
    if view_result_btn:
        debug_print(f"[DEBUG] Found view results button at {view_result_btn}")
        tap(view_result_btn[0], view_result_btn[1])
        time.sleep(0.5)
        for i in range(1):
            debug_print(f"[DEBUG] Clicking view results {i + 1}/3")
            triple_click(view_result_btn[0], view_result_btn[1], interval=0.01)
            time.sleep(0.01)
        debug_print("[DEBUG] Race preparation complete")
    else:
        debug_print("[DEBUG] View results button not found")

def after_race():
    """Handle post-race actions"""
    debug_print("[DEBUG] Handling post-race actions...")
    # Click next buttons using template matching
    click("assets/buttons/next_btn.png", confidence=0.7, minSearch=10)
    time.sleep(4)
    click("assets/buttons/next2_btn.png", confidence=0.7, minSearch=10)
    debug_print("[DEBUG] Post-race actions complete")

def career_lobby():
    """Main career lobby loop"""
    # Load configuration
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        MINIMUM_MOOD = config["minimum_mood"]
        PRIORITIZE_G1_RACE = config["prioritize_g1_race"]
    except Exception as e:
        print(f"Error loading config: {e}")
        MINIMUM_MOOD = "GREAT"
        PRIORITIZE_G1_RACE = False

    # Program start
    while True:
        debug_print("\n[DEBUG] ===== Starting new loop iteration =====")
        
        # First check, event - use intelligent event handling (same as original PC version)
        debug_print("[DEBUG] Checking for events...")
        try:
            # Use the same logic as original PC version: detect event first, then analyze
            event_choice_region = (6, 450, 126, 1776)
            event_icon = locate_on_screen("assets/icons/event_choice_1.png", confidence=0.45, region=event_choice_region)
            
            if event_icon:
                print("[INFO] Event detected, analyzing choices...")
                choice_number, success, choice_locations = handle_event_choice()
                if success:
                    click_success = click_event_choice(choice_number, choice_locations)
                    if click_success:
                        print(f"[INFO] Successfully selected choice {choice_number}")
                        time.sleep(0.5)
                        continue
                    else:
                        print("[WARNING] Failed to click event choice, falling back to top choice")
                        # Fallback to original method
                        event_choice_region = (6, 450, 126, 1776)
                        if click("assets/icons/event_choice_1.png", minSearch=2, text="[INFO] Event found, automatically select top choice.", region=event_choice_region):
                            continue
                else:
                    print("[WARNING] Event analysis failed, falling back to top choice")
                    # Fallback to original method
                    event_choice_region = (6, 450, 126, 1776)
                    if click("assets/icons/event_choice_1.png", minSearch=2, text="[INFO] Event found, automatically select top choice.", region=event_choice_region):
                        continue
            else:
                debug_print("[DEBUG] No events found")
        except Exception as e:
            print(f"[ERROR] Event handling error: {e}, falling back to original method")
            # Fallback to original method
            event_choice_region = (6, 450, 126, 1776)
            if click("assets/icons/event_choice_1.png", minSearch=2, text="[INFO] Event found, automatically select top choice.", region=event_choice_region):
                continue

        # Second check, inspiration
        debug_print("[DEBUG] Checking for inspiration...")
        if click("assets/buttons/inspiration_btn.png", confidence=0.5, minSearch=1, text="[INFO] Inspiration found."):
            continue

        debug_print("[DEBUG] Checking for next button...")
        if click("assets/buttons/next_btn.png", minSearch=1):
            continue

        debug_print("[DEBUG] Checking for cancel button...")
        if click("assets/buttons/cancel_btn.png", minSearch=1):
            continue

        # Check if current menu is in career lobby
        debug_print("[DEBUG] Checking if in career lobby...")
        tazuna_hint = locate_on_screen("assets/ui/tazuna_hint.png", confidence=0.8)

        if tazuna_hint is None:
            print("[INFO] Should be in career lobby.")
            continue

        debug_print("[DEBUG] Confirmed in career lobby")
        time.sleep(0.5)

        # Check if there is debuff status
        debug_print("[DEBUG] Checking for debuff status...")
        # Use match_template to get full bounding box for brightness check
        screenshot = take_screenshot()
        infirmary_matches = match_template(screenshot, "assets/buttons/infirmary_btn2.png", confidence=0.9)
        
        if infirmary_matches:
            debuffed_box = infirmary_matches[0]  # Get first match (x, y, w, h)
            x, y, w, h = debuffed_box
            center_x, center_y = x + w//2, y + h//2
            
            # Check if the button is actually active (bright) or just disabled (dark)
            if is_infirmary_active_adb(debuffed_box):
                tap(center_x, center_y)
                print("[INFO] Character has debuff, go to infirmary instead.")
                continue
            else:
                debug_print("[DEBUG] Infirmary button found but is disabled (dark)")
        else:
            debug_print("[DEBUG] No infirmary button detected")

        # Get current state
        debug_print("[DEBUG] Getting current game state...")
        mood = check_mood()
        mood_index = MOOD_LIST.index(mood)
        minimum_mood = MOOD_LIST.index(MINIMUM_MOOD)
        turn = check_turn()
        year = check_current_year()
        criteria = check_criteria()
        
        print("\n=======================================================================================\n")
        print(f"Year: {year}")
        print(f"Mood: {mood}")
        print(f"Turn: {turn}")
        print(f"Goal: {criteria}")
        debug_print(f"[DEBUG] Mood index: {mood_index}, Minimum mood index: {minimum_mood}")
        
        # Check if goals criteria are NOT met AND it is not Pre-Debut AND turn is less than 10
        # Prioritize racing when criteria are not met to help achieve goals
        debug_print("[DEBUG] Checking goal criteria...")
        criteria_met = (criteria.split(" ")[0] == "criteria" or "criteria met" in criteria.lower() or "goal achieved" in criteria.lower())
        year_parts = year.split(" ")
        is_pre_debut = "Pre-Debut" in year or "PreDebut" in year or "PreeDebut" in year or "PreeDebout" in year
        # Check if turn is a number before comparing
        turn_is_number = isinstance(turn, int) or (isinstance(turn, str) and turn.isdigit())
        turn_less_than_10 = turn < 10 if turn_is_number else False
        debug_print(f"[DEBUG] Year: '{year}', Criteria met: {criteria_met}, Pre-debut: {is_pre_debut}, Turn < 10: {turn_less_than_10}")
        
        if not criteria_met and not is_pre_debut and turn_less_than_10:
            print(f"Goal Status: Criteria not met - Prioritizing racing to meet goals")
            race_found = do_race()
            if race_found:
                print("Race Result: Found Race")
                continue
            else:
                print("Race Result: No Race Found")
                # If there is no race matching to aptitude, go back and do training instead
                click("assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
                time.sleep(0.5)
        else:
            print("Goal Status: Criteria met or conditions not suitable for racing")
        
        print("")

        # URA SCENARIO
        debug_print("[DEBUG] Checking for URA scenario...")
        if year == "Finale Season" and turn == "Race Day":
            print("[INFO] URA Finale")
            
            # Check skill points cap before URA race day (if enabled)
            enable_skill_check = config.get("enable_skill_point_check", True)
            
            if enable_skill_check:
                print("[INFO] URA Finale Race Day - Checking skill points cap...")
                check_skill_points_cap()
            
            # URA race logic would go here
            debug_print("[DEBUG] Starting URA race...")
            if click("assets/buttons/races_btn.png", minSearch=10):
                time.sleep(0.5)
                # Click race button 2 times after entering race menu
                for i in range(2):
                    if click("assets/buttons/race_btn.png", minSearch=2):
                        debug_print(f"[DEBUG] Successfully clicked race button {i+1}/2")
                        time.sleep(1)
                    else:
                        debug_print(f"[DEBUG] Race button not found on attempt {i+1}/2")
            
            race_prep()
            time.sleep(1)
            after_race()
            continue
        else:
            debug_print("[DEBUG] Not URA scenario")

        # If calendar is race day, do race
        debug_print("[DEBUG] Checking for race day...")
        if turn == "Race Day" and year != "Finale Season":
            print("[INFO] Race Day.")
            race_day()
            continue
        else:
            debug_print("[DEBUG] Not race day")

        # Mood check
        debug_print("[DEBUG] Checking mood...")
        if mood_index < minimum_mood:
            debug_print(f"[DEBUG] Mood too low ({mood_index} < {minimum_mood}), doing recreation")
            print("[INFO] Mood is low, trying recreation to increase mood")
            do_recreation()
            continue
        else:
            debug_print(f"[DEBUG] Mood is good ({mood_index} >= {minimum_mood})")

        # If Prioritize G1 Race is true, check G1 race every turn
        debug_print(f"[DEBUG] Checking G1 race priority: {PRIORITIZE_G1_RACE}")
        if PRIORITIZE_G1_RACE and "Pre-Debut" not in year and "PreDebut" not in year and "PreeDebut" not in year and "PreeDebout" not in year and is_racing_available(year):
            print("G1 Race Check: Looking for G1 race...")
            g1_race_found = do_race(PRIORITIZE_G1_RACE)
            if g1_race_found:
                print("G1 Race Result: Found G1 Race")
                continue
            else:
                print("G1 Race Result: No G1 Race Found")
                # If there is no G1 race, go back and do training
                click("assets/buttons/back_btn.png", text="[INFO] G1 race not found. Proceeding to training.")
                time.sleep(0.5)
        else:
            debug_print("[DEBUG] G1 race priority disabled or conditions not met")
        
        # Check training button
        debug_print("[DEBUG] Going to training...")
        if not go_to_training():
            print("[INFO] Training button is not found.")
            continue

        # Last, do training
        debug_print("[DEBUG] Analyzing training options...")
        time.sleep(0.5)
        results_training = check_training()
        
        debug_print("[DEBUG] Deciding best training action...")
        best_training = do_something(results_training)
        debug_print(f"[DEBUG] Best training decision: {best_training}")
        if best_training == "PRIORITIZE_RACE":
            debug_print("[DEBUG] Training logic suggests prioritizing race...")
            # Check if it's Pre-Debut - if so, don't prioritize racing
            year_parts = year.split(" ")
            if "Pre-Debut" in year or "PreDebut" in year or "PreeDebut" in year or "PreeDebout" in year:
                debug_print(f"[DEBUG] {year} detected, skipping race prioritization (no races available)")
                print(f"[INFO] {year} detected. Skipping race prioritization and proceeding to training.")
                # Re-evaluate training without race prioritization
                best_training = do_something_fallback(results_training)
                debug_print(f"[DEBUG] Fallback training decision: {best_training}")
                if best_training:
                    do_train(best_training)
                else:
                    do_rest()
                continue
            
            # Check if it's Finale Season - no races available, fall back to training without min_support
            if year == "Finale Season":
                debug_print("[DEBUG] Finale Season detected, no races available")
                print("[INFO] Finale Season detected. No races available. Proceeding to training without minimum support requirements.")
                # Re-evaluate training without race prioritization
                best_training = do_something_fallback(results_training)
                debug_print(f"[DEBUG] Fallback training decision: {best_training}")
                if best_training:
                    do_train(best_training)
                else:
                    do_rest()
                continue
            
            print("[INFO] Prioritizing race due to insufficient support cards.")
            
            # Check if all training options are unsafe before attempting race
            debug_print("[DEBUG] Checking if all training options are unsafe...")
            if all_training_unsafe(results_training):
                debug_print(f"[DEBUG] All training options have failure rate > {MAX_FAILURE}%")
                print(f"[INFO] All training options have failure rate > {MAX_FAILURE}%. Skipping race and choosing to rest.")
                do_rest()
                continue
            
            # Check if racing is available (no races in July/August)
            debug_print("[DEBUG] Checking if racing is available...")
            if not is_racing_available(year):
                debug_print("[DEBUG] Racing not available (summer break)")
                print("[INFO] July/August detected. No races available during summer break. Choosing to rest.")
                do_rest()
                continue
            
            print("Training Race Check: Looking for race due to insufficient support cards...")
            race_found = do_race()
            if race_found:
                print("Training Race Result: Found Race")
                continue
            else:
                print("Training Race Result: No Race Found")
                # If no race found, go back to training logic
                print("[INFO] No race found. Returning to training logic.")
                click("assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
                time.sleep(0.5)
                # Re-evaluate training without race prioritization
                best_training = do_something_fallback(results_training)
                debug_print(f"[DEBUG] Fallback training decision: {best_training}")
                if best_training:
                    do_train(best_training)
                else:
                    do_rest()
        elif best_training:
            debug_print(f"[DEBUG] Performing {best_training} training...")
            do_train(best_training)
        else:
            debug_print("[DEBUG] No suitable training found, doing rest...")
            do_rest()
        debug_print("[DEBUG] Waiting before next iteration...")
        time.sleep(1) 