
import json
import random
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
try:
    from colorama import Fore, init
except ImportError:
    class Fore:
        CYAN = YELLOW = GREEN = RED = MAGENTA = ""
    def init(**kwargs):
        pass
init(autoreset=True)
DESTINATIONS = {
    "beaches": ["Bali", "Maldives", "Phuket"],
    "mountains": ["Swiss Alps", "Rocky Mountains", "Himalayas"],
    "cities": ["Tokyo", "Paris", "New York"],
}
JOKES = [
    "Why don't programmers like nature? Too many bugs!",
    "Why did the computer go to the doctor? It had a virus!",
    "Why do travelers always feel warm? Because of all their hot spots!",
]
TIME_ZONES = {
    "zurich": "Europe/Zurich", "swiss alps": "Europe/Zurich",
    "paris": "Europe/Paris", "tokyo": "Asia/Tokyo",
    "new york": "America/New_York", "bali": "Asia/Makassar",
    "maldives": "Indian/Maldives", "phuket": "Asia/Bangkok",
    "rocky mountains": "America/Denver", "himalayas": "Asia/Kathmandu",
}
WEATHER_EXAMPLES = {
    "beaches": ["sunny, around 29°C", "partly cloudy, around 27°C"],
    "mountains": ["cool, around 9°C", "cloudy, around 5°C"],
    "cities": ["mild, around 19°C", "cloudy, around 16°C"],
}
DAILY_BUDGETS = {"budget": 65, "standard": 140, "comfort": 260}
HISTORY_PATH = Path("travelbot_history.json")
def normalize_input(text):
    return re.sub(r"\s+", " ", text.strip().lower())
def say(message, color=Fore.GREEN):
    print(color + "TravelBot: " + message)
def ask(prompt):
    return normalize_input(input(Fore.YELLOW + prompt))
def positive_or_negative(text):
    if re.search(r"\b(yes|yeah|yep|sure|ok|okay|love it|sounds good)\b", text):
        return True
    if re.search(r"\b(no|nope|nah|another|different)\b", text):
        return False
    return None
def recommend(memory):
    category = ask("Beaches, mountains, or cities? ")
    category = next((key for key in DESTINATIONS if re.search(rf"\b{key[:-1]}s?\b", category)), None)
    if category is None:
        say("Please choose beaches, mountains, or cities.", Fore.RED)
        return
    options = DESTINATIONS[category].copy()
    random.shuffle(options)
    for suggestion in options:
        memory["suggestions"].append(suggestion)
        say(f"How about {suggestion}?", Fore.CYAN)
        answer = positive_or_negative(ask("Do you like it? (yes/no) "))
        if answer is True:
            memory["last_destination"] = suggestion
            say(f"Awesome! Enjoy {suggestion}!")
            return
        if answer is None:
            say("I didn't understand that, so I'll try another suggestion.", Fore.RED)
        else:
            say("Let's try another destination!", Fore.CYAN)
    say("That's every suggestion in this category. Try another category!", Fore.MAGENTA)
def read_days():
    text = ask("How many days? ")
    if not re.fullmatch(r"\d+", text) or not 1 <= int(text) <= 365:
        say("Enter a whole number of days between 1 and 365.", Fore.RED)
        return None
    return int(text)
def packing_tips(memory):
    location = ask("Where are you going? (Enter for your last destination) ")
    location = location or memory["last_destination"]
    if not location:
        say("Please choose a destination first.", Fore.RED)
        return
    days = read_days()
    if days is None:
        return
    say(f"Packing ideas for {days} day(s) in {location.title()}:")
    for tip in ["Pack versatile clothes and comfortable shoes.",
                "Bring chargers, adapters and essential documents.",
                "Check the real forecast before departure.",
                "Pack enough essentials for your trip length."]:
        print(Fore.GREEN + "  - " + tip)
    memory["last_destination"] = location
def tell_joke(memory):
    joke = random.choice(JOKES)
    say(joke, Fore.YELLOW)
    memory["last_joke"] = joke
def weather(memory):
    location = ask("Destination or type (beaches/mountains/cities)? ")
    location = location or normalize_input(memory["last_destination"] or "")
    category = next((key for key, values in DESTINATIONS.items()
                     if location == key or location in [v.lower() for v in values]), None)
    if category is None:
        say("I only have examples for beaches, mountains and cities in my list.", Fore.RED)
        return
    say(f"SIMULATED weather example for {location.title()}: " +
        random.choice(WEATHER_EXAMPLES[category]) + ". Not a real forecast!", Fore.CYAN)
def local_time(memory):
    location = ask("Which destination? (Enter for your last destination) ")
    location = location or normalize_input(memory["last_destination"] or "")
    zone = TIME_ZONES.get(location)
    if not zone:
        say("I don't know that location. Try Tokyo, Paris, Bali or New York.", Fore.RED)
        return
    try:
        current = datetime.now(ZoneInfo(zone))
    except ZoneInfoNotFoundError:
        say("Time zone data is unavailable on this computer. Try installing tzdata.", Fore.RED)
        return
    say(f"Current local time in {location.title()}: {current:%Y-%m-%d %H:%M} ({current:%Z})")
def budget(memory):
    days = read_days()
    if days is None:
        return
    tier = ask("Budget level (budget/standard/comfort)? ")
    if tier not in DAILY_BUDGETS:
        say("Please choose budget, standard or comfort.", Fore.RED)
        return
    estimate = days * DAILY_BUDGETS[tier]
    say(f"Illustrative estimate: CHF {estimate:,} for {days} day(s), "
        "excluding transport to the destination. These are example rates, not quotes.")
    memory["last_budget"] = estimate
def save_history(memory):
    try:
        HISTORY_PATH.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")
        say(f"History saved to {HISTORY_PATH}.")
    except OSError as exc:
        say(f"Couldn't save history: {exc}", Fore.RED)
def load_history():
    blank = {"name": "", "last_destination": None, "suggestions": [], "last_joke": None,
             "last_budget": None, "messages": []}
    if not HISTORY_PATH.exists():
        return blank
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("History must be a JSON object")
        for key, default in blank.items():
            if key not in data or not isinstance(data[key], type(default)) and data[key] is not None:
                data[key] = default
        return data
    except (OSError, ValueError, TypeError) as exc:
        say(f"Could not load history ({exc}); starting fresh.", Fore.RED)
        return blank
def show_help():
    say("Commands: recommend, packing, joke, weather, time, budget, memory, "
        "save, help, exit.", Fore.MAGENTA)
    say("Weather and budget figures are examples; time uses your computer's time zone data.", Fore.CYAN)
COMMANDS = [
    (r"\b(recommend(?:ation)?s?|suggest(?:ion)?s?)\b", "recommend"),
    (r"\b(pack(?:ing)?|suitcase)\b", "packing"),
    (r"\b(joke|funny)\b", "joke"),
    (r"\b(weather|forecast)\b", "weather"),
    (r"\b(time|clock)\b", "time"),
    (r"\b(budget|cost|expense|price)\b", "budget"),
    (r"\b(memory|remember|history)\b", "memory"),
    (r"\b(save)\b", "save"),
    (r"\b(help|commands)\b", "help"),
    (r"\b(exit|bye|quit|goodbye)\b", "exit"),
]
def detect_intent(text):
    for pattern, intent in COMMANDS:
        if re.search(pattern, text):
            return intent
    return None
def chat():
    memory = load_history()
    say("Hello! I'm TravelBot.", Fore.CYAN)
    name = input(Fore.YELLOW + "Your name? ").strip()
    if name:
        memory["name"] = name
    name = memory["name"] or "Traveler"
    say(f"Nice to meet you, {name}!")
    show_help()
    handlers = {"recommend": recommend, "packing": packing_tips, "joke": tell_joke,
                "weather": weather, "time": local_time, "budget": budget}
    while True:
        try:
            message = ask(f"{name}: ")
        except (EOFError, KeyboardInterrupt):
            print()
            say("Goodbye!", Fore.CYAN)
            break
        if not message:
            continue
        memory["messages"].append(message)
        intent = detect_intent(message)
        if intent in handlers:
            handlers[intent](memory)
        elif intent == "help":
            show_help()
        elif intent == "memory":
            say(f"Last destination: {memory['last_destination'] or 'none'}; "
                f"recommendations made: {len(memory['suggestions'])}; "
                f"last budget: {memory['last_budget'] if memory['last_budget'] is not None else 'none'}")
        elif intent == "save":
            save_history(memory)
        elif intent == "exit":
            save_history(memory)
            say("Safe travels! Goodbye!", Fore.CYAN)
            break
        else:
            say("I didn't understand. Type 'help' for available commands.", Fore.RED)
if __name__ == "__main__":
    chat()