from sys import path as syspath
syspath.insert(0, '/Games/CatsEmblem')

print("GameState.py loaded")
from Shared import fetch_level, Cat, Dialog, Menu, Position, Stats, WeaponExp, classEnum, itemDict, get_cat, cat_sprite

_save_data = None

def get_save_data():
    global _save_data
    if _save_data is None:
        import thumbox
        thumbySaveData = thumbox.Thumby().saveData
        thumbySaveData.setName("CatsEmblem")
        _save_data = thumbySaveData
    return _save_data

# --- CONSTANTS ---
SCREEN_TILES_X = 9
SCREEN_TILES_Y = 5

class GameState:
    def __init__(
            self,
            level=None,
            party=None,
            state='title',
        ):
        self.bank = 0
        self.party = party if party else []
        self.selectedCatId: str | None = None
        self.load_level(level)
        self.player_turn = True
        self.cached_domain = None 
        self.combat_log = []
        self.dialog: list[Dialog] = []
        self.state = state
        self.menu = None
        self.lastPos = Position()

    def save_game(self):
        saveData = get_save_data()

        saveData.delItem("gameState-bank")
        saveData.delItem("gameState-level-number")
        saveData.delItem("gameState-party")

        saveData.setItem("gameState-bank", self.bank)
        saveData.setItem("gameState-level-number", self.level.number)
        saveData.setItem("gameState-party", [cat.name for cat in self.party])
        for cat in self.party:
            cat.save_state(saveData)
        saveData.save()

    def load_game(self):
        saveData = get_save_data()
        self.bank = saveData.getItem("gameState-bank")
        
        party_names: list[str] = saveData.getItem("gameState-party")
        
        party = []
        for cat_name in party_names:
            cat_stats = saveData.getItem(f"{cat_name}_stats")
            
            cat_items_names = saveData.getItem(f"{cat_name}_items")
            cat_item_durabilities = saveData.getItem(f"{cat_name}_durabilities")
            
            if len(cat_stats) == 21:
                stats = Stats(
                    attack=cat_stats[0],
                    defense=cat_stats[1],
                    max_hp=cat_stats[2],
                    speed=cat_stats[3],
                    luck=cat_stats[4],
                    range=cat_stats[5],
                )
                
                level = cat_stats[6]
                exp = cat_stats[7]
                next_level_exp = cat_stats[8]
                position = Position(cat_stats[9], cat_stats[10])
                
                items = [itemDict[item_name] for item_name in cat_items_names if item_name in itemDict]
                for i, item in enumerate(items):
                    if item.type == 'weapon' and i < len(cat_item_durabilities):
                        item.durability = cat_item_durabilities.pop(0)

                classType = 'pupil'
                for key, value in classEnum.items():
                    if value == cat_stats[11]:
                        classType = key
                        break
                
                weaponExp = WeaponExp(
                    sword=cat_stats[12],
                    repeater=cat_stats[13],
                    longbow=cat_stats[14],
                    bow=cat_stats[15],
                    lightning=cat_stats[16],
                    water=cat_stats[17],
                    earth=cat_stats[18],
                    mace=cat_stats[19],
                    spear=cat_stats[20]
                )
                
                loadedCat = Cat(
                    sprite=cat_sprite,
                    position=position,
                    name=cat_name,
                    stats=stats,
                    exp=exp,
                    level=level,
                    next_level_exp=next_level_exp,
                    items=items,
                    classType=classType,
                    weaponExp=weaponExp
                )
                party.append(loadedCat)
        
        self.party = party
        
        level_number = saveData.getItem("gameState-level-number")
        self.load_level(fetch_level(level_number))

    def has_saved_game(self):
        saveData = get_save_data()
        return (
            saveData.hasItem("gameState-level-number")
            and saveData.hasItem("gameState-party")
            and saveData.hasItem("gameState-bank")
            ## check that we have the stats and items for each cat in the party
            and all(
                saveData.hasItem(f"{cat_name}_stats") and saveData.hasItem(f"{cat_name}_items") and saveData.hasItem(f"{cat_name}_durabilities")
                for cat_name in saveData.getItem("gameState-party")
            )
        )

    def load_level(self, level=None):
        self.level = None
        self.cached_domain = None
        self.combat_log = []
        self.dialog = []
        self.menu = None
        if level is None:
            return
        for i, p in enumerate(self.party):
            p.set_position(level.startingPositions[i])
            p.restore_state()
        self.level = level
        self.update_selector_position(level.startingPositions[0].x, level.startingPositions[0].y)

    def set_state(self, new_state: str):
        if self.state == 'enemy-turn' and new_state == 'map':
            for unit in self.level.enemies:
                unit.set_exhausted(False)
                unit.set_moved(False)
        elif new_state == 'map':
            self.cancel_cat_select()
        elif new_state == 'enemy-turn':
            for cat in self.party:
                cat.set_exhausted(False)
                cat.set_moved(False)
        self.state = new_state

    def start_game(self):
        self.party = [get_cat()]
        self.load_level(fetch_level(1))

    def load_next_level(self):
        n = self.level.number
        if 1 <= n <= 6:
            self.load_level(fetch_level(n + 1))
            self.save_game()
        elif n == 7 and len(self.party) == 5:
            self.load_level(fetch_level(8))
            self.save_game()
        elif n == 7 or n == 8:
            self.load_level(fetch_level(9))
            self.save_game()
        elif n == 9:
            self.load_level(fetch_level(n + 1))
        elif n == 10:
            self.state = 'end'
        else:
            self.state = 'gameover'

    def add_dialog(self, dialog: 'Dialog'):
        self.dialog.append(dialog)

    def pop_dialog(self):
        if self.dialog:
            self.dialog.pop(0)

    def select_cat(self, cat: Cat):
        selCat = self.get_selected_cat()
        if selCat:
            selCat.set_selected(False)
            selCat.position = self.lastPos.copy()
        self.lastPos = self.level.selectorPosition.copy()
        cat.set_selected(True)
        self.selectedCatId = cat.id

    def cancel_cat_select(self):
        selCat = self.get_selected_cat()
        if selCat:
            selCat.set_selected(False)
            if not selCat.exhausted and selCat.moved and not selCat.enemy:
                selCat.moved = False
                selCat.position = self.lastPos.copy()
                GameState.update_selector_position(self, self.lastPos.x, self.lastPos.y)
        self.cached_domain = None
        self.selectedCatId = None
        self.lastPos = Position()

    def get_selected_cat(self):
        if not self.selectedCatId:
            return None
        enemies = self.level.enemies if self.level else []
        for c in self.party + enemies:
            if c.id == self.selectedCatId:
                return c
        return None

    def find_valid_positions(self, cat: Cat, range_distance: int):
        if not self.level:
            return []
        return self.level.find_valid_positions(cat, range_distance, self.party)

    def end_turn(self):
        self.cancel_cat_select()
        if len(self.level.enemies) == 0:
            for cat in self.party:
                cat.set_exhausted(False)
                cat.set_moved(False)
            self.add_dialog(Dialog(
                lines=["Player Turn"],
                overlay=True,
                timeout=1
            ))
            self.exit_menu()
        elif self.player_turn:
            for cat in self.party:
                cat.set_exhausted(False)
                cat.set_moved(False)
            self.player_turn = False
            self.set_state('enemy-turn')
            self.update_selector_position(self.level.enemies[0].position.x, self.level.enemies[0].position.y)
            self.add_dialog(Dialog(
                lines=[" Enemy Turn"],
                overlay=True,
                timeout=1
            ))
        else:
            for unit in self.level.enemies:
                unit.set_exhausted(False)
                unit.set_moved(False)
            self.player_turn = True
            self.set_state('map')
            self.update_selector_position(self.party[0].position.x, self.party[0].position.y)
            self.add_dialog(Dialog(
                lines=["Player Turn"],
                overlay=True,
                timeout=1
            ))

    def update_selector_position(self, x, y):
        new_x = max(0, min(len(self.level.map[0]) - 1, x))
        new_y = max(0, min(len(self.level.map) - 1, y))
        selCat = self.get_selected_cat()
        if self.state == 'map':
            if selCat and self.cached_domain:
                if (new_x, new_y) not in self.cached_domain:
                    return

            if selCat:
                for blockade in self.level.blockades:
                    if Position(new_x, new_y) in blockade.positions and not blockade.cleared:
                        return

        self.level.selectorPosition.x = new_x
        self.level.selectorPosition.y = new_y

        center_x = SCREEN_TILES_X // 2
        center_y = SCREEN_TILES_Y // 2

        viewport_x = max(0, min(len(self.level.map[0]) - SCREEN_TILES_X, new_x - center_x))
        viewport_y = max(0, min(len(self.level.map) - SCREEN_TILES_Y, new_y - center_y))

        self.level.viewport.x = viewport_x
        self.level.viewport.y = viewport_y

    def units_in_range(self, position: Position, range_distance: int):
        return [u for u in self.party + self.level.enemies
                if abs(u.position.x - position.x) + abs(u.position.y - position.y) <= range_distance]

    def cat_is_on_shop(self):
        cat = self.get_selected_cat()
        if not cat:
            return None
        for shop in self.level.shops:
            if cat.position == shop.position:
                return shop
        return None

    def update_bank(self, amount):
        self.bank += amount

    def cat_is_on_house(self):
        cat = self.get_selected_cat()
        if not cat:
            return None
        for house in self.level.houses:
            if cat.position == house.position:
                return house
        return None
    
    def enter_menu(self, menu: Menu):
        self.menu = menu
        self.state = 'menu'

    def exit_menu(self):
        self.menu = None
        self.state = 'map'

    def open_shop_menu(self, shop):
        import Menus
        Menus.install(GameState)
        return self.open_shop_menu(shop)

    def open_item_menu(self, option_index=0):
        import Menus
        Menus.install(GameState)
        return self.open_item_menu(option_index)

    def open_unit_menu(self, option_index=0):
        import Menus
        Menus.install(GameState)
        return self.open_unit_menu(option_index)

    def open_stats(self, unit=None):
        import Menus
        Menus.install(GameState)
        return self.open_stats(unit)

    def is_occupied(self, position: Position):
        return any(cat.position == position for cat in self.party + self.level.enemies)
