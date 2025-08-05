import pyautogui
import time
import json
import os
from pyautogui import ImageNotFoundException

pyautogui.useImageNotFoundException(False)

from core.state import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria, check_skill_points_cap
from core.logic import do_something, do_something_fallback, all_training_unsafe, MAX_FAILURE
from utils.constants import MOOD_LIST, EVENT_REGION, RACE_CARD_REGION, NEXT_BUTTON_CLICK_COORDS
# Event handling functions integrated directly into execute.py

def count_event_choices():
    """
    Count how many event choice icons are found on screen.
    Uses event_choice_1.png as template to find all U-shaped icons.
    
    Returns:
        tuple: (count, locations) - number of unique choices found and their locations
    """
    template_path = "assets/icons/event_choice_1.png"
    
    if not os.path.exists(template_path):
        return 0, []
    
    try:
        # Search for all instances of the template on screen
        locations = list(pyautogui.locateAllOnScreen(
            template_path, 
            confidence=0.8
        ))
        
        # Filter out duplicates (icons very close to each other)
        unique_locations = []
        for location in locations:
            center = pyautogui.center(location)
            is_duplicate = False
            
            for existing in unique_locations:
                existing_center = pyautogui.center(existing)
                distance = ((center.x - existing_center.x) ** 2 + (center.y - existing_center.y) ** 2) ** 0.5
                if distance < 30:  # Within 30 pixels
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_locations.append(location)
        
        return len(unique_locations), unique_locations
        
    except ImageNotFoundException:
        return 0, []
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
                
                recommendation_reason = f"All options have bad choices. Multiple options have same priority good choice. Selected based on tie-breaking (more good choices, then top choice)."
            else:
                best_option = best_options[0]
                recommendation_reason = f"All options have bad choices. Recommended based on highest priority good choice: '{option_analysis[best_option]['good_matches'][0]}'"
            
            recommended_option = best_option
        else:
            # No good choices found, recommend first option
            recommended_option = list(options.keys())[0]
            recommendation_reason = "All options have bad choices and no good choices found. Recommended first option."
    else:
        # Normal case: find option with highest priority good choice, but AVOID options with bad choices
        best_options = []  # Store all options with the same best priority
        best_priority = -1
        
        for option_name, analysis in option_analysis.items():
            # Only consider options that have good choices AND NO bad choices
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
                # Since all options have no bad choices, prefer option with more good choices
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
                
                recommendation_reason = f"Multiple options have same priority good choice. Selected based on tie-breaking (more good choices, then top choice)."
            else:
                best_option = best_options[0]
                recommendation_reason = f"Recommended based on highest priority good choice: '{option_analysis[best_option]['good_matches'][0]}'"
            
            recommended_option = best_option
        else:
            # No good options without bad choices found, recommend first option
            recommended_option = list(options.keys())[0]
            recommendation_reason = "No good options without bad choices found. Recommended first option."
    
    return {
        "recommended_option": recommended_option,
        "recommendation_reason": recommendation_reason,
        "option_analysis": option_analysis,
        "all_options_bad": all_options_bad
    }

def generate_event_variations(event_name):
    """Generate variations of the OCR result to handle common mistakes"""
    event_variations = [event_name]
    
    # Clean up common OCR artifacts first
    clean_name = event_name.strip().rstrip("'\"`").strip()
    if clean_name != event_name and clean_name not in event_variations:
        event_variations.append(clean_name)
    
    # Also try removing leading/trailing punctuation
    import re
    clean_name2 = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', clean_name).strip()
    if clean_name2 != clean_name and clean_name2 not in event_variations:
        event_variations.append(clean_name2)
    
    # Generate variations with smart character substitutions
    import re
    
    # Replace 'l' with '!' only at word boundaries or end of string
    if 'l' in event_name:
        # Replace 'l' at end of words or end of string
        variation = re.sub(r'l\b', '!', event_name)
        if variation != event_name and variation not in event_variations:
            event_variations.append(variation)
        
        # Also try replacing 'l' before punctuation
        variation2 = re.sub(r'l([!?.,])', r'!\1', event_name)
        if variation2 != event_name and variation2 not in event_variations:
            event_variations.append(variation2)
    
    # Replace '!' with 'l' (less common, but still try)
    if '!' in event_name:
        variation = event_name.replace('!', 'l')
        if variation not in event_variations:
            event_variations.append(variation)
    
    # Replace '%' with '☆' (OCR often reads ☆ as %)
    if '%' in event_name:
        variation = event_name.replace('%', '☆')
        if variation not in event_variations:
            event_variations.append(variation)
    
    # Replace '☆' with '%' (reverse case)
    if '☆' in event_name:
        variation = event_name.replace('☆', '%')
        if variation not in event_variations:
            event_variations.append(variation)
    
    # Also try removing extra characters that OCR might add
    # Remove multiple consecutive '!' or 'l' characters
    cleaned_variations = []
    for variation in event_variations:
        # Remove multiple consecutive '!' or 'l'
        cleaned = re.sub(r'[!l]{2,}', '!', variation)
        if cleaned not in event_variations and cleaned != variation:
            cleaned_variations.append(cleaned)
    
    event_variations.extend(cleaned_variations)
    
    # Try word order variations (common OCR issue)
    word_order_variations = []
    for variation in event_variations:
        words = variation.split()
        if len(words) >= 3:  # Only try reordering if we have enough words
            # Try different word orders
            if len(words) == 3:
                # For 3 words, try all permutations
                import itertools
                for perm in itertools.permutations(words):
                    perm_text = ' '.join(perm)
                    if perm_text not in event_variations and perm_text != variation:
                        word_order_variations.append(perm_text)
            elif len(words) == 4:
                # For 4+ words, try swapping first and last word groups
                first_half = ' '.join(words[:2])
                second_half = ' '.join(words[2:])
                swapped = f"{second_half} {first_half}"
                if swapped not in event_variations and swapped != variation:
                    word_order_variations.append(swapped)
    
    event_variations.extend(word_order_variations)
    
    return event_variations

def search_events(event_variations):
    """Search for matching events in databases"""
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
            
            if clean_db_name == clean_search_name or clean_db_name.endswith(clean_search_name) or clean_search_name in clean_db_name:
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
            
            if clean_db_name == clean_search_name or clean_db_name.endswith(clean_search_name) or clean_search_name in clean_db_name:
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
            
            if clean_db_name == clean_search_name or clean_db_name.endswith(clean_search_name) or clean_search_name in clean_db_name:
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
        tuple: (choice_number, success) - choice number (1, 2, 3, etc.) and whether successful
    """
    # Define the region for event name detection
    event_region = EVENT_REGION
    
    print("Event detected, scan event")
    
    try:
        # Wait for event to stabilize (1 second)
        time.sleep(1.0)
        
        # Capture the event name
        from utils.screenshot import capture_region
        from core.ocr import extract_event_name_text
        event_image = capture_region(event_region)
        event_name = extract_event_name_text(event_image)
        event_name = event_name.strip()
        
        if not event_name:
            print("No text detected in event region")
            return 1, False  # Default to first choice
        
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
                return choice_number, True
            else:
                print("No valid options found in database")
                return 1, False
        else:
            # Unknown event
            print("Unknown event - not found in database")
            print(f"Choices found: {choices_found}")
            return 1, False  # Default to first choice for unknown events
    
    except Exception as e:
        print(f"Error during event handling: {e}")
        return 1, False  # Default to first choice on error

def click_event_choice(choice_number):
    """
    Click on the specified event choice.
    
    Args:
        choice_number: The choice number to click (1, 2, 3, etc.)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find all event choice icons
        choice_locations = list(pyautogui.locateAllOnScreen(
            "assets/icons/event_choice_1.png", 
            confidence=0.8
        ))
        
        if not choice_locations:
            print("No event choice icons found")
            return False
        
        # Filter out duplicates
        unique_locations = []
        for location in choice_locations:
            center = pyautogui.center(location)
            is_duplicate = False
            
            for existing in unique_locations:
                existing_center = pyautogui.center(existing)
                distance = ((center.x - existing_center.x) ** 2 + (center.y - existing_center.y) ** 2) ** 0.5
                if distance < 30:  # Within 30 pixels
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_locations.append(location)
        
        # Sort locations by Y coordinate (top to bottom)
        unique_locations.sort(key=lambda loc: loc.top)
        
        # Click the specified choice
        if 1 <= choice_number <= len(unique_locations):
            target_location = unique_locations[choice_number - 1]
            center = pyautogui.center(target_location)
            
            print(f"Clicking choice {choice_number} at position ({center.x}, {center.y})")
            pyautogui.moveTo(center, duration=0.2)
            pyautogui.click()
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
from core.recognizer import is_infirmary_active, match_template
from utils.scenario import ura

with open("config.json", "r", encoding="utf-8") as file:
  config = json.load(file)

MINIMUM_MOOD = config["minimum_mood"]
PRIORITIZE_G1_RACE = config["prioritize_g1_race"]

def click(img, confidence = 0.8, minSearch = 2, click = 1, text = ""):
  btn = pyautogui.locateCenterOnScreen(img, confidence=confidence, minSearchTime=minSearch)
  if btn:
    if text:
      print(text)
    pyautogui.moveTo(btn, duration=0.175)
    pyautogui.click(clicks=click)
    return True
  
  return False

def go_to_training():
  return click("assets/buttons/training_btn.png")

def check_training():
  training_types = {
    "spd": "assets/icons/train_spd.png",
    "sta": "assets/icons/train_sta.png",
    "pwr": "assets/icons/train_pwr.png",
    "guts": "assets/icons/train_guts.png",
    "wit": "assets/icons/train_wit.png"
  }
  results = {}

  for key, icon_path in training_types.items():
    pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.8)
    if pos:
      pyautogui.moveTo(pos, duration=0.1)
      pyautogui.mouseDown()
      support_counts = check_support_card()
      total_support = sum(support_counts.values())
      
      # Retry failure detection if confidence is low
      max_retries = 3
      best_confidence = 0.0
      best_failure_result = None
      
      for attempt in range(max_retries):
        failure_result = check_failure()
        
        # Handle new tuple format (rate, confidence) or old format (rate)
        if isinstance(failure_result, tuple):
          failure_chance, confidence = failure_result
        else:
          failure_chance = failure_result
          confidence = 0.0  # Default confidence for old format
        
        # Keep the best result (highest confidence)
        if confidence > best_confidence:
          best_confidence = confidence
          best_failure_result = failure_result
        
        # If we have good confidence, no need to retry
        if confidence >= 0.5:
          break
        
        # Wait a bit before retry
        if attempt < max_retries - 1:
          time.sleep(0.2)
      
      # Use the best result we found
      if isinstance(best_failure_result, tuple):
        failure_chance, confidence = best_failure_result
      else:
        failure_chance = best_failure_result
        confidence = best_confidence
      
      results[key] = {
        "support": support_counts,
        "total_support": total_support,
        "failure": failure_chance,
        "confidence": confidence
      }
      
      retry_info = f" (retried {max_retries} times)" if best_confidence < 0.5 else ""
      print(f"[{key.upper()}] → {support_counts}, Fail: {failure_chance}% - Confident: {confidence:.2f}{retry_info}")
      time.sleep(0.1)
  
  pyautogui.mouseUp()
  click(img="assets/buttons/back_btn.png")
  return results

def do_train(train):
  train_btn = pyautogui.locateCenterOnScreen(f"assets/icons/train_{train}.png", confidence=0.8)
  if train_btn:
    pyautogui.tripleClick(train_btn, interval=0.1, duration=0.2)

def do_rest():
  rest_btn = pyautogui.locateCenterOnScreen("assets/buttons/rest_btn.png", confidence=0.8)
  rest_summber_btn = pyautogui.locateCenterOnScreen("assets/buttons/rest_summer_btn.png", confidence=0.8)

  if rest_btn:
    pyautogui.moveTo(rest_btn, duration=0.15)
    pyautogui.click(rest_btn)
  elif rest_summber_btn:
    pyautogui.moveTo(rest_summber_btn, duration=0.15)
    pyautogui.click(rest_summber_btn)

def do_recreation():
  recreation_btn = pyautogui.locateCenterOnScreen("assets/buttons/recreation_btn.png", confidence=0.8)
  recreation_summer_btn = pyautogui.locateCenterOnScreen("assets/buttons/rest_summer_btn.png", confidence=0.8)

  if recreation_btn:
    pyautogui.moveTo(recreation_btn, duration=0.15)
    pyautogui.click(recreation_btn)
  elif recreation_summer_btn:
    pyautogui.moveTo(recreation_summer_btn, duration=0.15)
    pyautogui.click(recreation_summer_btn)

def do_race(prioritize_g1 = False):
  click(img="assets/buttons/races_btn.png", minSearch=10)
  click(img="assets/buttons/ok_btn.png", minSearch=0.7)

  found = race_select(prioritize_g1=prioritize_g1)
  if not found:
    print("[INFO] No race found.")
    return False

  race_prep()
  time.sleep(1)
  after_race()
  return True

def race_day():
  # Check skill points cap before race day (if enabled)
  import json
  
  # Load config to check if skill point check is enabled
  with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)
  
  enable_skill_check = config.get("enable_skill_point_check", True)
  
  if enable_skill_check:
    print("[INFO] Race Day - Checking skill points cap...")
    check_skill_points_cap()
  
  click(img="assets/buttons/race_day_btn.png", minSearch=10)
  
  click(img="assets/buttons/ok_btn.png", minSearch=0.7)
  time.sleep(0.5)

  for i in range(2):
    click(img="assets/buttons/race_btn.png", minSearch=2)
    time.sleep(0.5)

  race_prep()
  time.sleep(1)
  after_race()

def race_select(prioritize_g1 = False):
  pyautogui.moveTo(x=560, y=680)

  time.sleep(0.2)

  if prioritize_g1:
    print("[INFO] Looking for G1 race.")
    for i in range(2):
      race_card = match_template("assets/ui/g1_race.png", threshold=0.9)

      if race_card:
        for x, y, w, h in race_card:
          region = (x, y, RACE_CARD_REGION[2], RACE_CARD_REGION[3])
          match_aptitude = pyautogui.locateCenterOnScreen("assets/ui/match_track.png", confidence=0.8, minSearchTime=0.7, region=region)
          if match_aptitude:
            print("[INFO] G1 race found.")
            pyautogui.moveTo(match_aptitude, duration=0.2)
            pyautogui.click()
            for i in range(2):
              race_btn = pyautogui.locateCenterOnScreen("assets/buttons/race_btn.png", confidence=0.8, minSearchTime=2)
              if race_btn:
                pyautogui.moveTo(race_btn, duration=0.2)
                pyautogui.click(race_btn)
                time.sleep(0.5)
            return True
      
      for i in range(4):
        pyautogui.scroll(-300)
    
    return False
  else:
    print("[INFO] Looking for race.")
    for i in range(4):
      match_aptitude = pyautogui.locateCenterOnScreen("assets/ui/match_track.png", confidence=0.8, minSearchTime=0.7)
      if match_aptitude:
        print("[INFO] Race found.")
        pyautogui.moveTo(match_aptitude, duration=0.2)
        pyautogui.click(match_aptitude)

        for i in range(2):
          race_btn = pyautogui.locateCenterOnScreen("assets/buttons/race_btn.png", confidence=0.8, minSearchTime=2)
          if race_btn:
            pyautogui.moveTo(race_btn, duration=0.2)
            pyautogui.click(race_btn)
            time.sleep(0.5)
        return True
      
      for i in range(4):
        pyautogui.scroll(-300)
    
    return False

def race_prep():
  view_result_btn = pyautogui.locateCenterOnScreen("assets/buttons/view_results.png", confidence=0.8, minSearchTime=20)
  if view_result_btn:
    pyautogui.click(view_result_btn)
    time.sleep(0.5)
    for i in range(3):
      pyautogui.tripleClick(interval=0.2)
      time.sleep(0.3)

def after_race():
  # Try to click next_btn.png, if not found, click at (185, 900) and wait for it to appear
  if not click(img="assets/buttons/next_btn.png", minSearch=10):
    print(f"[INFO] next_btn.png not found, clicking at {NEXT_BUTTON_CLICK_COORDS} and waiting...")
    pyautogui.click(NEXT_BUTTON_CLICK_COORDS[0], NEXT_BUTTON_CLICK_COORDS[1])
    time.sleep(1)  # Wait a bit for the button to appear
    click(img="assets/buttons/next_btn.png", minSearch=10)
  
  time.sleep(0.5) # Raise a bit
  pyautogui.click()
  click(img="assets/buttons/next2_btn.png", minSearch=10)

def career_lobby():
  # Program start
  while True:
    # First check, event - use intelligent event handling
    try:
      event_icon = pyautogui.locateCenterOnScreen("assets/icons/event_choice_1.png", confidence=0.8, minSearchTime=0.2)
      if event_icon:
        print("[INFO] Event detected, analyzing choices...")
        choice_number, success = handle_event_choice()
        if success:
          click_success = click_event_choice(choice_number)
          if click_success:
            print(f"[INFO] Successfully selected choice {choice_number}")
            time.sleep(0.5)
            continue
          else:
            print("[WARNING] Failed to click event choice, falling back to top choice")
            # Fallback to original method
            if click(img="assets/icons/event_choice_1.png", minSearch=0.2, text="[INFO] Event found, automatically select top choice."):
              continue
        else:
          print("[WARNING] Event analysis failed, falling back to top choice")
          # Fallback to original method
          if click(img="assets/icons/event_choice_1.png", minSearch=0.2, text="[INFO] Event found, automatically select top choice."):
            continue
    except Exception as e:
      print(f"[ERROR] Event handling error: {e}, falling back to original method")
      # Fallback to original method
      if click(img="assets/icons/event_choice_1.png", minSearch=0.2, text="[INFO] Event found, automatically select top choice."):
        continue

    # Second check, inspiration
    if click(img="assets/buttons/inspiration_btn.png", minSearch=0.2, text="[INFO] Inspiration found."):
      continue

    if click(img="assets/buttons/next_btn.png", minSearch=0.2):
      continue

    if click(img="assets/buttons/cancel_btn.png", minSearch=0.2):
      continue

    # Check if current menu is in career lobby
    tazuna_hint = pyautogui.locateCenterOnScreen("assets/ui/tazuna_hint.png", confidence=0.8, minSearchTime=0.2)

    if tazuna_hint is None:
      print("[INFO] Should be in career lobby.")
      continue

    time.sleep(0.5)

    # Check if there is debuff status
    debuffed = pyautogui.locateOnScreen("assets/buttons/infirmary_btn2.png", confidence=0.9, minSearchTime=1)
    if debuffed:
      if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
        pyautogui.click(debuffed)
        print("[INFO] Character has debuff, go to infirmary instead.")
        continue

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
    
    # Check if goals criteria are NOT met AND it is not Pre-Debut AND turn is less than 10
    # Prioritize racing when criteria are not met to help achieve goals
    criteria_met = (criteria.split(" ")[0] == "criteria" or "criteria met" in criteria.lower() or "goal achieved" in criteria.lower())
    year_parts = year.split(" ")
    is_pre_debut = "Pre-Debut" in year
    if not criteria_met and not is_pre_debut and turn < 10:
      print(f"Goal Status: Criteria not met - Prioritizing racing to meet goals")
      race_found = do_race()
      if race_found:
        print("Race Result: Found Race")
        continue
      else:
        print("Race Result: No Race Found")
        # If there is no race matching to aptitude, go back and do training instead
        click(img="assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
        time.sleep(0.5)
    else:
      print("Goal Status: Criteria met or conditions not suitable for racing")
    
    print("")

    # URA SCENARIO
    if year == "Finale Season" and turn == "Race Day":
      print("[INFO] URA Finale")
      
      # Check skill points cap before URA race day (if enabled)
      import json
      
      # Load config to check if skill point check is enabled
      with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)
      
      enable_skill_check = config.get("enable_skill_point_check", True)
      
      if enable_skill_check:
        print("[INFO] URA Finale Race Day - Checking skill points cap...")
        check_skill_points_cap()
      
      ura()
      for i in range(2):
        if click(img="assets/buttons/race_btn.png", minSearch=2):
          time.sleep(0.5)
      
      race_prep()
      time.sleep(1)
      after_race()
      continue

    # If calendar is race day, do race
    if turn == "Race Day" and year != "Finale Season":
      print("[INFO] Race Day.")
      race_day()
      continue

    # Mood check
    if mood_index < minimum_mood:
      print("[INFO] Mood is low, trying recreation to increase mood")
      do_recreation()
      continue



    year_parts = year.split(" ")
    # If Prioritize G1 Race is true, check G1 race every turn
    if PRIORITIZE_G1_RACE and "Pre-Debut" not in year and is_racing_available(year):
      print("G1 Race Check: Looking for G1 race...")
      g1_race_found = do_race(PRIORITIZE_G1_RACE)
      if g1_race_found:
        print("G1 Race Result: Found G1 Race")
        continue
      else:
        print("G1 Race Result: No G1 Race Found")
        # If there is no G1 race, go back and do training
        click(img="assets/buttons/back_btn.png", text="[INFO] G1 race not found. Proceeding to training.")
        time.sleep(0.5)
    
    # Check training button
    if not go_to_training():
      print("[INFO] Training button is not found.")
      continue

    # Last, do training
    time.sleep(0.5)
    results_training = check_training()
    
    best_training = do_something(results_training)
    if best_training == "PRIORITIZE_RACE":
      # Check if it's Pre-Debut - if so, don't prioritize racing
      year_parts = year.split(" ")
      if "Pre-Debut" in year:
        print("[INFO] Pre-Debut detected. Skipping race prioritization and proceeding to training.")
        # Re-evaluate training without race prioritization
        best_training = do_something_fallback(results_training)
        if best_training:
          go_to_training()
          time.sleep(0.5)
          do_train(best_training)
        else:
          do_rest()
        continue
      
      # Check if it's Finale Season - no races available, fall back to training without min_support
      if year == "Finale Season":
        print("[INFO] Finale Season detected. No races available. Proceeding to training without minimum support requirements.")
        # Re-evaluate training without race prioritization
        best_training = do_something_fallback(results_training)
        if best_training:
          go_to_training()
          time.sleep(0.5)
          do_train(best_training)
        else:
          do_rest()
        continue
      
      print("[INFO] Prioritizing race due to insufficient support cards.")
      
      # Check if all training options are unsafe before attempting race
      if all_training_unsafe(results_training):
        print(f"[INFO] All training options have failure rate > {MAX_FAILURE}%. Skipping race and choosing to rest.")
        do_rest()
        continue
      
      # Check if racing is available (no races in July/August)
      if not is_racing_available(year):
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
        click(img="assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
        time.sleep(0.5)
        # Re-evaluate training without race prioritization
        best_training = do_something_fallback(results_training)
        if best_training:
          go_to_training()
          time.sleep(0.5)
          do_train(best_training)
        else:
          do_rest()
    elif best_training:
      go_to_training()
      time.sleep(0.5)
      do_train(best_training)
    else:
      do_rest()
    time.sleep(1)
