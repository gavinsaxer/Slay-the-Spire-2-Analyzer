from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError

class Badge(BaseModel):
    id: str
    rarity: str

class Card(BaseModel):
    name: str
    upgraded: bool
    enchantment: str | None

class Potion(BaseModel):
    name: str

class CardChoice(BaseModel):
    floor: int
    picked: Card
    not_picked: List[Card] = Field(default_factory=list)

class PotionChoice(BaseModel):
    floor: int
    picked: List[Potion] = Field(default_factory=list)
    not_picked: List[Potion] = Field(default_factory=list)

class PotionUse(BaseModel):
    floor: int
    potion : Potion

class PotionDiscard(BaseModel):
    floor: int
    potion: Potion

class CampfireChoice(BaseModel):
    floor: int
    picked: str
    data: RelicObtained | CardChoice | Card | None

class EventChoice(BaseModel):
    floor: int
    name: str
    choice: str
    damage: int = 0
    max_hp_lost: int = 0

class AncientChoice(BaseModel):
    act: int
    picked: str
    not_picked: List[str]

class RelicObtained (BaseModel):
    floor: int
    name: str

class MonsterEncounter(BaseModel):
    floor: int
    enemies: List[str]
    type: str
    turns: int
    damage: int

class ItemPurchase(BaseModel):
    floor: int
    type: str
    name: str
    price: int #might only be able to get price for entire shop purchase


class RunData(BaseModel):
    character_chosen: str
    ascension_level: int
    victory: bool
    floor_reached: int
    playtime: int
    abandonded: bool
    # Nested lists of sub-models
    card_choices: List[CardChoice] = Field(default_factory=list)
    potion_choices: List[PotionChoice] = Field(default_factory=list)
    potions_used: List[PotionUse] = Field(default_factory=list)
    potions_discarded: List[PotionDiscard] = Field(default_factory=list)
    campfire_choices: List[CampfireChoice] = Field(default_factory=list)
    event_choices: List[EventChoice] = Field(default_factory=list)
    ancient_choices: List[AncientChoice] = Field(default_factory=list)
    relics: List[RelicObtained] = Field(default_factory=list)
    monsters: List[MonsterEncounter] = Field(default_factory=list)
    master_deck: List[Card] = Field(default_factory=list)
    badges: List[Badge] = Field(default_factory=list)

    @property
    def deck_size(self) -> int:
        return len(self.master_deck)
