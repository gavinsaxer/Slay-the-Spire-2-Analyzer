import json
import logging
from pathlib import Path
from typing import List
from pydantic import ValidationError

from core.schemas import *

def parse_sts2_run(raw_json: dict) -> RunData:
    """Parses a raw Slay the Spire 2 JSON into the flat RunData schema."""

    player_data = raw_json["players"][0]

    # 1. Extract High-Level Metadata
    run_args = {
        "character_chosen": player_data["character"],
        "ascension_level": raw_json.get("ascension", 0),
        "victory": raw_json["win"],
        "floor_reached": sum(len(act) for act in raw_json.get("map_point_history", [])),
        "playtime": raw_json["run_time"],
        "abandonded": raw_json.get("was_abandoned",False),
        # "master_deck": player_data.get("deck", []),
        #event_choices
        "badges": player_data.get("badges", []),
        "monsters": [],
        "card_choices": [],
        "campfire_choices": [],
        "potion_choices": [],
        "potions_used": [],
        "potions_discarded":[],
        "relics":[],
        "ancient_choices":[]
    }

    # 2. Iterate chronologically to determine the Floor
    act = 1
    floor = 1
    for floor_array in raw_json.get("map_point_history", []):
        print("On act", act)

        for point in floor_array:
            map_point_type = point.get("map_point_type")

            # Player stats and room info for this specific floor
            stats = point.get("player_stats", [{}])[0]
            room = point.get("rooms", [{}])[0]

            # --- EXTRACT COMBATS ---
            if map_point_type in ["monster", "elite", "boss"]:
                run_args["monsters"].append(
                    MonsterEncounter(
                        floor=floor,
                        type=map_point_type,
                        enemies=[enemy for enemy in room.get("monster_ids", []) if enemy!="MONSTER.OSTY"],
                        turns=room.get("turns_taken", 0),
                        damage=stats.get("damage_taken", 0),
                    )
                )

            # --- EXTRACT CAMPFIRES ---
            if map_point_type == "rest_site" and "rest_site_choices" in stats:
                action = stats["rest_site_choices"][0]  # e.g. "HEAL" or "SMITH"

                # If they upgraded, pull the card ID
                upgraded_card = None
                if action == "SMITH" and "upgraded_cards" in stats:
                    upgraded_card = Card(name = stats["upgraded_cards"][0], upgraded = True, enchantment= None )

                run_args["campfire_choices"].append(
                    CampfireChoice(floor=floor, picked=action, data=upgraded_card)
                )

            # --- EXTRACT CARD CHOICES --- maybe alter behavior for shops
            if "card_choices" in stats:
                picked = None
                not_picked = []

                for choice in stats["card_choices"]:
                    card = Card(name = choice["card"]["id"], upgraded= False, enchantment=None)
                    if choice["was_picked"]:
                        picked = card
                    else:
                        not_picked.append(card)

                if picked:
                    run_args["card_choices"].append(
                        CardChoice(floor=floor, picked=picked, not_picked=not_picked)
                    )

            # Extract Potions Choices maybe alter behavior for shops
            if "potion_choices" in stats:
                picked = []
                not_picked = []

                for choice in stats["potion_choices"]:
                    potion = Potion(name = choice["choice"])
                    if choice["was_picked"]:
                        picked.append(potion)
                    else:
                        not_picked.append(potion)
                if picked:
                    run_args["potion_choices"].append(
                        PotionChoice(floor=floor, picked=picked, not_picked=not_picked)
            )

            # Extract Potions Used and Discarded
            if "potion_used" in stats:
                run_args["potions_used"].extend(
                    [PotionUse(floor = floor, potion = Potion(name = item)) for item in stats["potion_used"]]
                )
            if "potion_discarded" in stats:
                run_args["potions_discarded"].extend(
                    [PotionDiscard(floor = floor, potion = Potion(name = item)) for item in stats["potion_discarded"]]
                )

            # Extract Relic Pickups
            if "relic_choices" in stats:
                run_args["relics"].extend([RelicObtained(floor = floor, name = relic["choice"]) for relic in stats["relic_choices"] if relic["was_picked"]])

            # Extract Ancient Choices
            if map_point_type == "ancient":
                picked = ""
                not_picked = []
                for choice in stats["ancient_choice"]:
                    if choice["was_chosen"]:
                        picked = choice["TextKey"]
                    else:
                        not_picked.append(choice["TextKey"])
                run_args["ancient_choices"].append(AncientChoice(floor=floor, picked=picked, not_picked=not_picked))

            floor+=1
        act+=1

        # You would continue mapping event_choices, potions, and shop purchases here
        # using the 'stats' dictionary.

    # 3. Pass the structured dictionary into Pydantic for validation
    return RunData(**run_args)


def test_single_run(file_path: str) -> RunData | None:
    """Reads a file and routes it through the adapter."""
    path = Path(file_path)

    if not path.is_file():
        print(f"File not found: {path.absolute()}")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_json = json.load(f)

        # The adapter function handles the translation AND validation
        run = parse_sts2_run(raw_json)

        # Prints out your clean, strictly typed Pydantic object
        print(run)


    except json.JSONDecodeError:
        print("Error: The file has invalid JSON syntax.")
    except ValidationError as e:
        print(f"Schema Mismatch Error:\n{e}")
    except KeyError as e:
        print(f"Missing expected JSON key during parsing: {e}")



# Usage:
test_single_run("test_runs/example1.run")
