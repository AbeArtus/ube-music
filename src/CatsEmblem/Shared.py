from sys import path as syspath
from MapData import button_sprite_sheet, cat_head_sprite_sheet, cat_sprite_sheet, enemy_sprite_sheet, tileEncumberence, canWalkOn
import thumbox
Sprite = thumbox.Thumby().Sprite
import gc

syspath.insert(0, '/Games/CatsEmblem')

classEnum = {
    'pupil': 0,
    'warrior': 1,
    'sniper': 2,
    'wizard': 3
}

from Items import Item, itemDict

_class_overlay_data = None

def get_class_overlay_data():
    global _class_overlay_data
    if _class_overlay_data is None:
        _class_overlay_data = {
            (True, 'wizard'): (bytearray([255, 231, 208, 140, 141, 141, 204, 224]), bytearray([0, 0, 16, 0, 0, 0, 0, 0])),
            (True, 'sniper'): (bytearray([255, 135, 123, 255, 255, 255, 255, 255]), bytearray([32, 0, 32, 0, 0, 0, 0, 0])),
            (True, 'warrior'): (bytearray([207, 175, 143, 159, 159, 159, 255, 255]), bytearray([0, 32, 0, 0, 0, 0, 0, 0])),
            (False, 'wizard'): (bytearray([255, 255, 231, 193, 194, 206, 206, 238]), bytearray([0, 0, 24, 62, 63, 49, 49, 17])),
            (False, 'sniper'): (bytearray([255, 135, 123, 255, 255, 255, 255, 255]), bytearray([32, 120, 164, 0, 0, 0, 0, 0])),
            (False, 'warrior'): (bytearray([255, 207, 143, 159, 191, 159, 255, 255]), bytearray([0, 48, 112, 112, 96, 96, 0, 0])),
        }
    return _class_overlay_data

classAdvantages = {
    'warrior': ['wizard', 'pupil'],
    'sniper': ['warrior', 'pupil'],
    'wizard': ['sniper', 'pupil'],
}

class Position:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, Position):
            return self.x == other.x and self.y == other.y
        return False

    def __hash__(self):
        return hash((self.x, self.y))

    def copy(self):
        return Position(self.x, self.y)

class Stats:
    def __init__(
            self,
            attack: int = 3,
            defense: int = 2,
            max_hp: int = 8,
            speed: int = 3,
            luck: int = 2,
            range: int = 3
        ):
        self.attack = attack
        self.defense = defense
        self.max_hp = max_hp
        self.speed = speed
        self.luck = luck
        self.range = range


class GrowthRates:
    def __init__(
            self,
            attack: int = 40,
            defense: int = 40,
            max_hp: int = 60,
            speed: int = 60,
            luck: int = 30,
            range: int = 20
        ):
        self.attack = attack
        self.defense = defense
        self.max_hp = max_hp
        self.speed = speed
        self.luck = luck
        self.range = range

class WeaponExp:
    def __init__(
            self,
            sword: int = 0,
            repeater: int = 0,
            longbow: int = -1,
            bow: int = -1,
            lightning: int = -1,
            water: int = -1,
            earth: int = -1,
            mace: int = -1,
            spear: int = -1
        ):
            self.sword = sword
            self.repeater = repeater
            self.longbow = longbow
            self.bow = bow
            self.lightning = lightning
            self.water = water
            self.earth = earth
            self.mace = mace
            self.spear = spear

    def get_weapon_exp(self, weapon_type: str) -> int:
        if hasattr(self, weapon_type):
            return getattr(self, weapon_type)
        return -1

    def get_weapon_attack_bonus(self, weapon_type: str) -> int:
        exp = self.get_weapon_exp(weapon_type)
        if exp == -1:
            return 0
        elif exp < 10:
            return 0
        elif exp < 50:
            return 0.05
        elif exp < 100:
            return 0.10
        elif exp < 200:
            return 0.15
        else:
            return 0.20

    def increase_exp(self, weapon_type: str, amount: int = 1):
        if hasattr(self, weapon_type):
            current_exp = getattr(self, weapon_type)
            if current_exp >= 0:
                setattr(self, weapon_type, current_exp + amount)
    def add_weapons(self, weapon_types):
        for weapon_type in weapon_types:
            if hasattr(self, weapon_type):
                if getattr(self, weapon_type) == -1:
                    setattr(self, weapon_type, 0)

class Option:
    def __init__(self, label, action, condition=lambda: True):
        self.label = label
        self.action = action
        self.condition = condition

class Menu:
    def __init__(self, options, title=None, option_index=0, menu_index=0, leave_action=None):
        self.options = options
        self.title = title if title else [lambda: ""]
        self.option_index = option_index
        self.menu_index = menu_index
        self.leave_action = leave_action

    def get_options(self):
        return [opt for opt in self.options[self.menu_index] if opt.condition()]

    def get_visible_options(self, max_visible: int = 4):
        valid_options = self.get_options()
        offset = max(0, self.option_index - max_visible + 1)
        return valid_options[offset:offset + max_visible], offset

class Cat:
    _id_counter = 0  # Class variable for unique IDs

    def __init__(
        self,
        sprite,
        position,
        name,
        selected=False,
        exhausted=False,
        stats=None,
        enemy=False,
        level=1,
        exp=0,
        next_level_exp=20,
        aiType='stand',
        aiPath=None,
        items=None,
        classType='pupil',
        weaponExp=None,
        growthRates=None
    ):
        self.id = f"cat_{Cat._id_counter}"  # Generate a sequential ID
        Cat._id_counter += 1
        self._sprite = None
        self._sprite_factory = None
        if callable(sprite):
            self._sprite_factory = sprite
        else:
            self._sprite = sprite
        self.position = position
        self.selected = selected
        self.exhausted = exhausted
        self.name = name
        self.stats = stats if stats is not None else Stats()
        self.growthRates = growthRates if growthRates is not None else GrowthRates()
        self.enemy = enemy
        self.hp = self.stats.max_hp
        self.exp = exp
        self.moved = False
        self.level = level
        self.next_level_exp = next_level_exp
        self.aiType = aiType
        self.aiPath = aiPath if aiPath else []
        self.items: list[Item] = (items if items else [])[:4]
        self.max_items = 4
        self.classType = classType
        self.weaponExp = weaponExp if weaponExp else WeaponExp()
        self._class_sprite = None
        self._class_sprite_key = None

    @property
    def sprite(self):
        if self._sprite is None and self._sprite_factory is not None:
            self._sprite = self._sprite_factory()
        return self._sprite

    @sprite.setter
    def sprite(self, value):
        self._sprite = value
        self._sprite_factory = None

    def save_state(self, saveData):
        saveData.delItem(f"{self.name}_stats")
        saveData.delItem(f"{self.name}_items")
        saveData.delItem(f"{self.name}_durabilities")

        saveData.setItem(f"{self.name}_stats", [
            self.stats.attack,
            self.stats.defense,
            self.stats.max_hp,
            self.stats.speed,
            self.stats.luck,
            self.stats.range,
            self.level,
            self.exp,
            self.next_level_exp,
            self.position.x,
            self.position.y,
            classEnum[self.classType] if self.classType in classEnum else 0,
            self.weaponExp.sword,
            self.weaponExp.repeater,
            self.weaponExp.longbow,
            self.weaponExp.bow,
            self.weaponExp.lightning,
            self.weaponExp.water,
            self.weaponExp.earth,
            self.weaponExp.mace,
            self.weaponExp.spear,
        ])
        saveData.setItem(f"{self.name}_items", [item.name for item in self.items])
        saveData.setItem(f"{self.name}_durabilities", [item.durability for item in self.items if item.type == 'weapon'])

    def equip_item(self, item_index: int):
        temp = self.items[0]
        self.items[0] = self.items[item_index]
        self.items[item_index] = temp

    def restore_state(self):
        self.set_exhausted(False)
        self.set_moved(False)
        self.set_hp(self.stats.max_hp)
        self.set_selected(False)

    def getClassSprite(self, position: Position = Position(0, 0)):
        sprite_key = (self.enemy, self.classType)
        sprite_data = get_class_overlay_data().get(sprite_key)
        if sprite_data is None:
            return None

        if self._class_sprite is None or self._class_sprite_key != sprite_key:
            self._class_sprite = Sprite(8, 8, sprite_data, position.x, position.y, key=1)
            self._class_sprite_key = sprite_key
        else:
            self._class_sprite.x = position.x
            self._class_sprite.y = position.y
        return self._class_sprite

    def use_item(self, item_index):
        if item_index < 0 or item_index >= len(self.items):
            return

        item = self.items[item_index]
        if item.type == 'consumable' and item.effect and 'heal' in item.effect:
            self.hp = min(self.stats.max_hp, self.hp + item.effect['heal'])
            self.items.pop(item_index)
        if item.type == 'consumable' and item.effect and 'luck' in item.effect:
            self.stats.luck += item.effect['luck']
            self.items.pop(item_index)
        if item.type == 'consumable' and item.effect and 'defense' in item.effect:
            self.stats.defense += item.effect['defense']
            self.items.pop(item_index)
        if item.type == 'consumable' and item.effect and 'attack' in item.effect:
            self.stats.attack += item.effect['attack']
            self.items.pop(item_index)
        if item.type == 'consumable' and item.effect and 'speed' in item.effect:
            self.stats.speed += item.effect['speed']
            self.items.pop(item_index)
        if item.type == 'consumable' and item.effect and 'level' in item.effect:
            self.add_exp(item.effect['level'] * 20)

    def set_position(self, position: Position):
        self.position = position

    def set_moved(self, moved):
        self.moved = moved

    def set_exhausted(self, exhausted):
        self.exhausted = exhausted

    def set_selected(self, selected):
        self.selected = selected

    def set_enemy(self, enemy):
        self.enemy = enemy

    def set_sprite_position(self, position):
        self.sprite.x = position.x
        self.sprite.y = position.y

    def set_hp(self, new_hp):
        self.hp = min(new_hp, self.stats.max_hp)

    def advance_animation(self):
        curFrame = self.sprite.getFrame()
        nextFrame = (curFrame + 1) % self.sprite.frameCount
        self.sprite.setFrame(nextFrame)

    def add_exp(self, amount, addDialog=None):
        levels_gained = ((self.exp % 20) + amount) // 20
        self.exp += amount

        for _ in range(levels_gained):
            self.level_up(addDialog)

        return self

    def get_weapon(self):
        for item in self.items:
            if item.type == 'weapon' and item.can_use(self.classType):
                return item
        return None

    def level_up(self, addDialog=None):
        import random
        self.level += 1
        self.next_level_exp += 20

        RN = random.randint(1, 100)
        CF = random.randint(20, 80)
        luck = getattr(self.stats, 'luck', 0)

        if not self.enemy and addDialog:
            addDialog([f"{self.name} level up", f"to {self.level}"], self)
        for stat in ['attack', 'defense', 'max_hp', 'speed', 'luck', 'range']:
            RN = (RN + CF) % 100
            added = 0
            if RN <= getattr(self.growthRates, stat):
                setattr(self.stats, stat, getattr(self.stats, stat) + 1)
                added += 1
                if RN < luck and stat != 'range':
                    setattr(self.stats, stat, getattr(self.stats, stat) + 1)
                    added += 1
            if added > 0 and stat == 'max_hp':
                self.hp += added
            if added > 0 and not self.enemy and addDialog:
                currentValue = getattr(self.stats, stat)
                addDialog([f"{stat} up",f"from {currentValue - added}", f"to {currentValue}!"], self)
    
    def can_move(self):
        return not self.exhausted and not self.moved

    def promote(self, new_class: str):
        self.classType = new_class
        self.classSprite = self.getClassSprite(self.position)
        self.exp = 0
        self.next_level_exp = 12
        if new_class == 'warrior':
            self.stats.attack += 2
            self.stats.defense += 2
            self.stats.max_hp += 3
            self.weaponExp.add_weapons(['spear', 'mace'])
        elif new_class == 'sniper':
            self.stats.attack += 2
            self.stats.speed += 2
            self.stats.luck += 1
            self.weaponExp.add_weapons(['longbow', 'bow'])
        elif new_class == 'wizard':
            self.stats.attack += 2
            self.stats.max_hp += 2
            self.stats.luck += 1
            self.weaponExp.add_weapons(['lightning', 'water', 'earth'])

class Dialog:
    def __init__(
        self,
        lines=None,
        left_cats=None,
        right_cats=None,
        currentlyTalking='',
        decision=True,
        lambda_after=None,
        overlay=False,
        timeout=None
    ):
        self.lines = lines if lines else []
        self.currentlyTalking = currentlyTalking
        self.left_cats = left_cats if left_cats else []
        self.right_cats = right_cats if right_cats else []
        self.lambda_after = lambda_after
        self.decision = decision
        self.overlay = overlay
        self.timeout = timeout

class House:
    def __init__(
        self,
        position,
        preVisitedDialogs=None,
        dialogs=None,
        postVisitDialog=None,
        visitCondition=None,
        multipleVisits=False,
        destroyed=False
    ):
        self.position = position
        self.dialogs = dialogs if dialogs else []
        self.preVisitedDialogs = preVisitedDialogs if preVisitedDialogs else []
        self.postVisitDialog = postVisitDialog if postVisitDialog else []
        def defaultVisitCondition(): return True
        self.visitCondition = visitCondition if visitCondition else defaultVisitCondition
        self.multipleVisits = multipleVisits
        self.visited = False
        self.destroyed = destroyed

    def visit(self):
        if self.multipleVisits:
            self.visited = False
            return
        self.visited = True

    def can_visit(self):
        if self.destroyed:
            return False
        if self.preVisitedDialogs and not self.visited:
            return True
        if self.visitCondition and not self.visited:
            return self.visitCondition()
        if self.visited and self.postVisitDialog:
            return True
        return self.destroyed

    def destroy(self):
        self.destroyed = True
        self.dialogs = []
        self.preVisitedDialogs = []
        self.postVisitDialog = []
        self.visitCondition = lambda: False

class ShopItem:
    def __init__(self, item: Item, price: int):
        self.item: Item = item
        self.price: int = price

class Shop:
    def __init__(
        self,
        position: Position,
        inventory: list[ShopItem] = [],
    ):
        self.position = position
        self.inventory = inventory

# --- CLASSES ---

class AttackLog:
    def __init__(
        self,
        attacker_name: str,
        attacker_hp: int,
        attacker_max_hp: int,
        attacker_enemy: bool,
        attacker_sprite: Sprite,
        defender_name: str,
        defender_hp: int,
        defender_max_hp: int,
        defender_enemy: bool,
        defender_sprite: Sprite,
        damage: int,
        old_hp: int,
        new_hp: int,
        miss: bool,
        dodge: bool,
        text: str,
        static_render_time: int = 0
    ):
        self.attacker_name = attacker_name
        self.attacker_hp = attacker_hp
        self.attacker_max_hp = attacker_max_hp
        self.attacker_enemy = attacker_enemy
        self.attacker_sprite = attacker_sprite
        self.defender_name = defender_name
        self.defender_hp = defender_hp
        self.defender_max_hp = defender_max_hp
        self.defender_enemy = defender_enemy
        self.defender_sprite = defender_sprite
        self.damage = damage
        self.old_hp = old_hp
        self.new_hp = new_hp
        self.miss = miss
        self.dodge = dodge
        self.text = text
        self.static_render_time = static_render_time

class Button:
    def __init__(self, position, pressed=None, pressAction=None, unPressAction=None, canUnpress=None, canPress=None):
        self.position = position
        self.pressed = False if pressed is None else pressed
        self.pressAction = pressAction
        self.canPress = canPress if canPress is not None else True
        self.unPressAction = unPressAction
        self.canUnpress = canUnpress if canUnpress is not None else True

    def press(self):
        if self.pressed:
            if not self.unPressAction:
                return
            self.unPressAction()
            self.pressed = False
        else:
            if not self.canPress:
                return
            self.pressed = True
            if self.pressAction:
                self.pressAction()

    def can_press(self):
        if self.pressed:
            return self.canUnpress
        else:
            return self.canPress

class Blockade:
    def __init__(self, positions, cleared=None):
        self.positions = positions
        self.cleared = cleared if cleared is not None else False

    def clear(self):
        self.cleared = True

    def unclear(self):
        self.cleared = False

class OverlayObject:
    def __init__(self, position, objectName, boundPositions):
        self.position = position
        self.objectName = objectName
        self.boundPositions = boundPositions

class Conversation:
    def __init__(
        self,
        dialogs,
        nameOne='',
        nameTwo='',
        condition=lambda: True
    ):
        self.dialogs = dialogs
        self.nameOne = nameOne
        self.nameTwo = nameTwo
        self.condition = condition

class Level:
    def __init__(
        self,
        map,
        enemies,
        number=1,
        seizePosition=Position(1, 1),
        startingPositions=None,
        shops=None,
        houses=None,
        conversations=None,
        buttons=None,
        blockades=None,
        overlayObjects=None
    ):
        self.map = map
        self.enemies = enemies
        self.viewport = Position()
        self.selectorPosition = Position()
        self.number = number
        self.seizePosition = seizePosition
        self.startingPositions = startingPositions if startingPositions else []
        self.shops = shops if shops else []
        self.houses = houses if houses else []
        self.conversations = conversations if conversations else []
        self.buttons = buttons if buttons is not None else []
        self.blockades = blockades if blockades is not None else []
        self.overlayObjects = overlayObjects if overlayObjects is not None else []

    def find_valid_positions(self, cat: Cat, range: int, party: list[Cat]):
        map_width = len(self.map[0])
        map_height = len(self.map)

        def is_walkable(position):
            if not (0 <= position.x < map_width and 0 <= position.y < map_height):
                return False
            tile = self.map[position.y][position.x]
            return tile in canWalkOn and canWalkOn[tile]

        def get_occupying_unit(position):
            for unit in party + self.enemies:
                if unit.id != cat.id and unit.position == position:
                    return unit
            return None

        def is_barrier(position):
            for blockade in self.blockades:
                if position in blockade.positions and not blockade.cleared:
                    return True
            return False

        visited = set()
        valid_positions = set()
        position_weight = dict()
        queue = [(cat.position, range)]

        while queue:
            current_pos, remaining_range = queue.pop(0)

            if remaining_range < 0 or (current_pos in visited and position_weight.get(f"{current_pos.x},{current_pos.y}", -1) >= remaining_range):
                continue

            visited.add(current_pos)
            position_weight[f"{current_pos.x},{current_pos.y}"] = remaining_range

            if not is_walkable(current_pos):
                continue

            occupying_unit = get_occupying_unit(current_pos)
            occupied_by_enemy = occupying_unit is not None and occupying_unit.enemy != cat.enemy
            occupied_by_ally = occupying_unit is not None and occupying_unit.enemy == cat.enemy

            if is_barrier(current_pos):
                continue

            # Allies can be passed through but cannot be a final standing tile.
            if occupied_by_enemy:
                continue
            if not occupied_by_ally or (occupied_by_ally and not cat.enemy) or current_pos == cat.position:
                valid_positions.add(current_pos)

            if remaining_range > 0:
                neighbors = []
                if current_pos.x >= cat.position.x:
                    neighbors.append(Position(current_pos.x + 1, current_pos.y))
                if current_pos.x <= cat.position.x:
                    neighbors.append(Position(current_pos.x - 1, current_pos.y))
                if current_pos.y >= cat.position.y:
                    neighbors.append(Position(current_pos.x, current_pos.y + 1))
                if current_pos.y <= cat.position.y:
                    neighbors.append(Position(current_pos.x, current_pos.y - 1))
                for neighbor in neighbors:
                    if is_walkable(neighbor):
                        encumbrance = tileEncumberence.get(self.map[neighbor.y][neighbor.x], 1)
                        queue.append((neighbor, remaining_range - encumbrance))

        return list(valid_positions)

def cat_sprite(): return Sprite(8, 8, cat_sprite_sheet(), 32, 16, key=1)
def enemy_sprite(): return Sprite(8, 8, enemy_sprite_sheet(), 32, 16, key=1)
def button_sprite(pos): return Sprite(8, 8, button_sprite_sheet(), pos.x, pos.y)
def cat_head(pos): return Sprite(40, 40, cat_head_sprite_sheet(), pos.x, pos.y, 1)

# --- UNITS (lazy) ---
_unit_cache = {}

def _build_cat_unit():
    return Cat(
        sprite=cat_sprite,
        position=Position(2, 4),
        name='cat',
        stats=Stats(defense=5, attack=4, speed=4, luck=3, range=4),
        growthRates=GrowthRates(attack=45, defense=45, luck=50, range=15),
        items=[itemDict['Stick'], itemDict['Tuna']],
    )

def _build_tac_unit():
    return Cat(
        sprite=cat_sprite,
        position=Position(5, 13),
        name='tac',
        stats=Stats(defense=3, attack=5, speed=5, luck=3, range=4),
        growthRates=GrowthRates(defense=50, speed=70, luck=25, range=25),
        items=[itemDict['Slngsht']]
    )

def _build_mew_unit():
    return Cat(
        sprite=cat_sprite,
        name='mew',
        position=Position(3, 1),
        stats=Stats(attack=4, max_hp=10, speed=4, range=4, defense=3),
        items=[itemDict['Stick']],
        weaponExp=WeaponExp(repeater=10, sword=20),
        growthRates=GrowthRates(attack=50, speed=65, range=15)
    ).add_exp(40, None)

def _build_bub_unit():
    return Cat(
        sprite=cat_sprite,
        name='bub',
        position=Position(8, 14),
        stats=Stats(attack=4, defense=4, speed=4, luck=4, range=4),
        enemy=False,
        classType='sniper',
        items=[itemDict['Repeater'], itemDict['Tuna']],
        growthRates=GrowthRates(attack=60, defense=30, max_hp=55, speed=45, luck=40, range=30),
        weaponExp=WeaponExp(bow=10, longbow=50, repeater=35, sword=10)
    ).add_exp(100, None)


def _build_bao_unit():
    return Cat(
        sprite=cat_sprite,
        name='bao',
        position=Position(8,14),
        stats=Stats(attack=5, defense=4, luck=4, range=4),
        enemy=False,
        aiType='stand',
        classType='wizard',
        items=[itemDict['EarthTm'], itemDict['Tuna']],
        growthRates=GrowthRates(attack=45, defense=45, max_hp=65, speed=50, luck=50),
        weaponExp=WeaponExp(lightning=60, water=20, earth=35, sword=10, repeater=15)
    ).add_exp(80, None)

def _build_npc_unit():
    return Cat(
        sprite=cat_sprite,
        name='npc',
        position=Position(0, 0),
        enemy=False,
        items=[]
    )

def _get_or_create_unit(unit_name: str, factory):
    if unit_name not in _unit_cache:
        _unit_cache[unit_name] = factory()
    return _unit_cache[unit_name]

def get_cat():
    return _get_or_create_unit('cat', _build_cat_unit)

def get_tac():
    return _get_or_create_unit('tac', _build_tac_unit)

def get_mew():
    return _get_or_create_unit('mew', _build_mew_unit)

def get_bub():
    return _get_or_create_unit('bub', _build_bub_unit)

def get_bao():
    return _get_or_create_unit('bao', _build_bao_unit)

def get_npc():
    return _get_or_create_unit('npc', _build_npc_unit)

class PathPoint:
    def __init__(self, position: Position):
        self.position = position
        self.visited = False

    def mark_visited(self):
        self.visited = True

def generate_enemy(level: int, position: Position, ai='searchAndDestroy', name='pig', weapon="Stick", classType='pupil', path=None):
    enemySprite = enemy_sprite()
    bigBoiPath = []
    if path is not None:
        for p in path:
            bigBoiPath.append(PathPoint(p))
    e = Cat(
        sprite=enemySprite,
        position=position,
        name=name,
        enemy=True,
        aiType=ai,
        items=[itemDict[weapon]],
        classType=classType,
        aiPath=bigBoiPath
    )
    e.add_exp((level - 1) * 20, None)
    return e


def fetch_level(level_number):
    import sys
    from Callbacks import CALLBACKS
    if level_number < 6:
        sys.modules.pop('ActTwo', None)
        gc.collect()
        from ActOne import ActOneLevels, set_game_state_callbacks
        set_game_state_callbacks(*CALLBACKS)
        levels = ActOneLevels

        if level_number == 1:
            return levels._build_level1()
        elif level_number == 2:
            return levels._build_level2()
        elif level_number == 3:
            return levels._build_level3()
        elif level_number == 4:
            return levels._build_level4()
        elif level_number == 5:
            return levels._build_level5()
        return None
    else:
        sys.modules.pop('ActOne', None)
        gc.collect()
        from ActTwo import ActTwoLevels, set_game_state_callbacks
        set_game_state_callbacks(*CALLBACKS)
        levels = ActTwoLevels

        if level_number == 6:
            return levels._build_level6()
        elif level_number == 7:
            return levels._build_level7()
        elif level_number == 8:
            return levels._build_level8()
        elif level_number == 9:
            return levels._build_level9()
        elif level_number == 10:
            return levels._build_level10()
        else:
            return None
