weaponAdvantages = {
    'sword': 'mace',
    'spear': 'sword',
    'mace': 'spear',
    'longbow': 'bow',
    'bow': 'repeater',
    'repeater': 'longbow',
    'lightning': 'water',
    'water': 'earth',
    'earth': 'lightning'
}

class Item:
    def __init__(self, name: str, item_type: str, effect=None, attack=0, accuracy=0, range=1, crit=0, allowedClasses=None, weaponType: str=None, durability: int =None):
        self.name = name
        self.type = item_type
        self.effect = effect
        self.attack = attack
        self.accuracy = accuracy
        self.range = range
        self.crit = crit
        self.allowedClasses = allowedClasses if allowedClasses else ['pupil']
        self.weaponType = weaponType
        self.durability = durability if durability is not None else 0  # None means infinite durability

    def can_use(self, classType: str):
        return classType in self.allowedClasses

    def can_counter(self, other_weapon_type: str):
        if self.weaponType in weaponAdvantages:
            return weaponAdvantages[self.weaponType] == other_weapon_type
        return False

    def use_weapon(self):
        if self.durability is not None:
            self.durability -= 1
            if self.durability <= 0:
                return True  # Weapon is broken
        return False  # Weapon is still usable

    def get_range(self):
        if self.range == 12:
            return [1, 2]
        return [self.range]

    def clone(self):
        return Item(
            name=self.name,
            item_type=self.type,
            effect=self.effect.copy() if isinstance(self.effect, dict) else self.effect,
            attack=self.attack,
            accuracy=self.accuracy,
            range=self.range,
            crit=self.crit,
            allowedClasses=list(self.allowedClasses),
            weaponType=self.weaponType,
            durability=self.durability,
        )

_item_cache = {}

def _build_item(item_name: str):
    if item_name == "Stick":
        return Item(name="Stick", item_type="weapon", attack=2, accuracy=80, range=1, crit=0, allowedClasses=['pupil', 'warrior', 'sniper', 'wizard'], weaponType='sword', durability=20)
    if item_name == "Slngsht":
        return Item(name="Slngsht", item_type="weapon", attack=1, accuracy=75, range=2, crit=1, allowedClasses=['pupil', 'sniper', 'warrior', 'wizard'], weaponType='repeater', durability=20)
    if item_name == "LghtngTm":
        return Item(name="LghtngTm", item_type="weapon", attack=4, accuracy=80, range=2, crit=5, allowedClasses=['wizard'], weaponType='lightning', durability=15)
    if item_name == "WaterTm":
        return Item(name="WaterTm", item_type="weapon", attack=3, accuracy=85, range=12, crit=3, allowedClasses=['wizard'], weaponType='water', durability=15)
    if item_name == "EarthTm":
        return Item(name="EarthTm", item_type="weapon", attack=5, accuracy=70, range=12, crit=2, allowedClasses=['wizard'], weaponType='earth', durability=15)
    if item_name == "LongBow":
        return Item(name="LongBow", item_type="weapon", attack=3, accuracy=80, range=3, crit=5, allowedClasses=['sniper'], weaponType='longbow', durability=15)
    if item_name == "Bow":
        return Item(name="Bow", item_type="weapon", attack=5, accuracy=85, range=2, crit=3, allowedClasses=['sniper'], weaponType='bow', durability=15)
    if item_name == "Repeater":
        return Item(name="Repeater", item_type="weapon", attack=3, accuracy=75, range=12, crit=4, allowedClasses=['sniper'], weaponType='repeater', durability=20)
    if item_name == "Sword":
        return Item(name="Sword", item_type="weapon", attack=6, accuracy=85, range=1, crit=5, allowedClasses=['warrior', 'pupil'], weaponType='sword', durability=20)
    if item_name == "Spear":
        return Item(name="Spear", item_type="weapon", attack=5, accuracy=60, range=2, crit=3, allowedClasses=['warrior'], weaponType='spear', durability=15)
    if item_name == "Mace":
        return Item(name="Mace", item_type="weapon", attack=4, accuracy=75, range=12, crit=2, allowedClasses=['warrior'], weaponType='mace', durability=15)
    if item_name == "NecTome":
        return Item(name="NecTome", item_type="weapon", attack=5, accuracy=90, range=12, crit=5, allowedClasses=['wizard'], weaponType='earth', durability=5)
    if item_name == "BulTome":
        return Item(name="BulTome", item_type="weapon", attack=4, accuracy=85, range=3, crit=4, allowedClasses=['wizard'], weaponType='water', durability=10)
    if item_name == "MultiShot":
        return Item(name="MultiShot", item_type="weapon", attack=2, accuracy=80, range=12, crit=3, allowedClasses=['sniper'], weaponType='repeater', durability=10)
    if item_name == "Launcher":
        return Item(name="Launcher", item_type="weapon", attack=5, accuracy=70, range=3, crit=2, allowedClasses=['sniper'], weaponType='longbow', durability=4)
    if item_name == "Axe":
        return Item(name="Axe", item_type="weapon", attack=4, accuracy=75, range=12, crit=4, allowedClasses=['warrior'], weaponType='mace', durability=15)
    if item_name == "VoidSwd":
        return Item(name="VoidSwd", item_type="weapon", attack=7, accuracy=80, range=1, crit=5, allowedClasses=['warrior'], weaponType='sword', durability=5)
    if item_name == "Tuna":
        return Item(name="Tuna", item_type="consumable", effect={"heal": 10})
    if item_name == "MystPot":
        return Item(name="MystPot", item_type="promote", effect={"promote": "wizard"})
    if item_name == "MstMeal":
        return Item(name="MstMeal", item_type="promote", effect={"promote": "warrior"})
    if item_name == "MstQll":
        return Item(name="MstQll", item_type="promote", effect={"promote": "sniper"})
    if item_name == "MagPowder":
        return Item(name="MagPowder", item_type="consumable", effect={"level": 1})
    if item_name == "RabFoot":
        return Item(name="RabFoot", item_type="consumable", effect={"luck": 3})
    if item_name == "Armor":
        return Item(name="Armor", item_type="consumable", effect={"defense": 3})
    if item_name == "PowerRing":
        return Item(name="PowerRing", item_type="consumable", effect={"attack": 3})
    if item_name == "NewBal":
        return Item(name="NewBal", item_type="consumable", effect={"speed": 3})
    raise KeyError(item_name)

class LazyItemDict:
    def __contains__(self, key):
        return key in {
            "Stick", "Slngsht", "LghtngTm", "WaterTm", "EarthTm",
            "LongBow", "Bow", "Repeater", "Sword", "Spear", "Mace",
            "MagPowder", "RabFoot", "Armor", "PowerRing", "NewBal",
            "NecTome", "BulTome", "MultiShot", "Launcher", "Axe", "VoidSwd",
            "Tuna", "MystPot", "MstMeal", "MstQll"
        }

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        if key not in _item_cache:
            _item_cache[key] = _build_item(key)
        return _item_cache[key].clone()  # Return a clone to avoid shared state issues

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

itemDict = LazyItemDict()
