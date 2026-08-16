import gc
from sys import path as syspath
syspath.insert(0, '/Games/CatsEmblem')

from Shared import fetch_level, Cat, Dialog, Menu, Option, Position, Shop, Stats, WeaponExp, classEnum, itemDict, get_cat, cat_sprite, Level
from MapData import canWalkOn, tileEncumberence

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

        nextLevel = fetch_level(level_number)
        self.load_level(nextLevel)

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

    def load_level(self, level: Level | None):
        if level is None:
            self.level = None
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
                if Position(new_x, new_y) not in self.cached_domain:
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

    def open_shop_menu(self, shop: Shop):
        shop_menu_options: list[Option] = []

        def exit_menu():
            selCat = self.get_selected_cat()
            selCat.set_exhausted(True)
            self.cancel_cat_select()
            self.exit_menu()

        for shop_item in shop.inventory:
            def make_purchase_action(item=shop_item):
                def purchase():
                    
                    selCat = self.get_selected_cat()
                    if selCat and len(selCat.items) >= 4:
                        self.add_dialog(Dialog(
                            left_cats=[selCat],
                            currentlyTalking=selCat.name,
                            lines=["Inventory", "Full!"],
                        ))
                        return
                    if self.bank >= item.price:
                        self.update_bank(-item.price)
                        selCat.items.append(item.item)
                        self.add_dialog(Dialog(
                            left_cats=[selCat],
                            currentlyTalking=selCat.name,
                            lines=[f"Purchased",
                                   f"{item.item.name}!"],
                        ))
                    else:
                        self.add_dialog(Dialog(
                            left_cats=[selCat],
                            currentlyTalking=selCat.name,
                            lines=["Not enough",
                                   "gold!"],
                        ))
                return purchase

            shop_menu_options.append(Option(
                label= f"{shop_item.price} {shop_item.item.name}",
                action= make_purchase_action(),
                condition= lambda: True
            ))
        self.enter_menu(menu = Menu(
            options=[shop_menu_options],
            title= [lambda: f"Shop {self.bank}G"],
            leave_action=exit_menu
        ))

    def open_item_menu(self, option_index=0):
        selectedCat = self.get_selected_cat()
        if selectedCat:
            item_menu_options: list[Option] = []
            current_option_index = self.menu.option_index if self.menu else 0

            def exit_menu():
                self.open_unit_menu(current_option_index)

            for i, item in enumerate(selectedCat.items):
                def open_item_action_menu(index=i):
                    if selectedCat.exhausted and item.type in ['consumable', 'promote']:
                        return lambda: None
                    def item_action_menu():
                        item = selectedCat.items[index]
                        item_action_options: list[Option] = []

                        if item.effect and item.type == 'consumable' and not selectedCat.exhausted:
                            def use_item_action():
                                def use_item():
                                    selectedCat.use_item(index)
                                    selectedCat.set_exhausted(True)
                                    exit_menu()
                                return use_item()

                            item_action_options.append(Option(
                                label= "Use",
                                action= use_item_action,
                                condition= lambda: not selectedCat.exhausted
                            ))
                        if item.type == 'weapon' and index != 0:
                            def equip_item_action(item_index=index):
                                def equip_item(item_index=item_index):
                                    temp = selectedCat.items[0]
                                    selectedCat.items[0] = selectedCat.items[item_index]
                                    selectedCat.items[item_index] = temp

                                    self.state = 'map'
                                return equip_item

                            item_action_options.append(Option(
                                label= "Equip",
                                action= equip_item_action(index),
                                condition= lambda: item.can_use(selectedCat.classType)
                            ))
                        if item.type == 'promote' and selectedCat.level >= 5 and selectedCat.classType == 'pupil':
                            def promote_action():
                                def promote():
                                    promotion_class = item.effect.get('promote', '')
                                    selectedCat.promote(promotion_class)
                                    selectedCat.items.pop(index)
                                    self.add_dialog(Dialog(
                                        left_cats=[selectedCat],
                                        currentlyTalking=selectedCat.name,
                                        lines=["*promoted to", f"{promotion_class}*"],
                                    ))
                                    self.state = 'map'
                                    selectedCat.set_exhausted(True)
                                    self.selectedCatId = None
                                return promote

                            item_action_options.append(Option(
                                label= "Promote",
                                action= promote_action(),
                                condition= lambda: not selectedCat.exhausted
                            ))

                        neighbors = [
                            Position(selectedCat.position.x + 1, selectedCat.position.y),
                            Position(selectedCat.position.x - 1, selectedCat.position.y),
                            Position(selectedCat.position.x, selectedCat.position.y + 1),
                            Position(selectedCat.position.x, selectedCat.position.y - 1),
                        ]
                        nearby_party_members = [
                            p for p in self.party if p.position in neighbors and p != selectedCat
                        ]
                        if nearby_party_members:
                            def trade_item_action(item_index=index):
                                def trade_item():
                                    trade_target_options: list[Option] = []
                            
                                    for target_cat in nearby_party_members:
                                        def select_target_cat(target=target_cat):
                                            def open_trade_with_target(target=target_cat):
                                                target_item_options: list[Option] = []
                            
                                                for target_item_index, target_item in enumerate(target.items):
                                                    def select_target_item(target_index=target_item_index):
                                                        def perform_trade():
                                                            selected_item = selectedCat.items[item_index]
                                                            target_item = target.items[target_index]
                                                            selectedCat.items[item_index] = target_item
                                                            target.items[target_index] = selected_item
                                                        
                                                            selectedCat.set_exhausted(True)
                                                            self.state = 'map'
                                                            self.selectedCatId = None
                            
                                                        return perform_trade
                            
                                                    target_item_options.append(Option(
                                                        label= target_item.name if target_item else "--",
                                                        action= select_target_item(target_item_index),
                                                        condition= lambda: True
                                                    ))

                                                if len(target.items) < target.max_items:
                                                    def trade_with_empty_slot():
                                                        def perform_trade_with_empty():
                                                            selected_item = selectedCat.items[item_index]
                                                            target.items.append(selected_item)
                                                            selectedCat.items.pop(item_index)

                                                            selectedCat.set_exhausted(True)
                                                            self.selectedCatId = None
                                                            self.state = 'map'
                            
                                                        return perform_trade_with_empty
                            
                                                    target_item_options.append(Option(
                                                        label= "--",
                                                        action= trade_with_empty_slot(),
                                                        condition= lambda: True
                                                    ))
                            
                                                self.enter_menu(menu=Menu(
                                                    options=[target_item_options],
                                                    title=[lambda: f"Trade with {target.name}"],
                                                    leave_action=lambda: self.open_item_menu(index)
                                                ))
                            
                                            return open_trade_with_target
                            
                                        trade_target_options.append(Option(
                                            label= target_cat.name,
                                            action= select_target_cat(target_cat),
                                            condition= lambda: True
                                        ))
                            
                                    self.enter_menu(menu=Menu(
                                        options=[trade_target_options],
                                        title=[lambda: "Select Trade Target"],
                                        leave_action=lambda: self.open_item_menu(index)
                                    ))
                            
                                return trade_item

                            item_action_options.append(Option(
                                label= "Trade",
                                action= trade_item_action(index),
                                condition= lambda: not selectedCat.exhausted
                            ))

                        def open_item_stats_menu(sel_item=item):
                            stats_options: list[Option] = [
                                Option(label=f"type:{sel_item.type}", action=lambda: None)
                            ]

                            if sel_item.type == 'weapon':
                                stats_options.extend([
                                    Option(label=f"dur:{sel_item.durability}", action=lambda: None),
                                    Option(label=f"atk:{sel_item.attack}", action=lambda: None),
                                    Option(label=f"acc:{sel_item.accuracy}", action=lambda: None),
                                    Option(label=f"rng:{sel_item.range}", action=lambda: None),
                                    Option(label=f"crt:{sel_item.crit}", action=lambda: None),
                                ])
                            elif sel_item.type == 'consumable' and sel_item.effect and 'heal' in sel_item.effect:
                                stats_options.append(Option(label=f"heal:{sel_item.effect['heal']}", action=lambda: None))
                            elif sel_item.type == 'promote' and sel_item.effect and 'promote' in sel_item.effect:
                                stats_options.append(Option(label=f"class:{sel_item.effect['promote']}", action=lambda: None))

                            stats_options.append(Option(label="Back", action=lambda: self.open_item_menu(index)))
                            self.enter_menu(menu=Menu(
                                options=[stats_options],
                                title=[lambda: f"{sel_item.name} Stats"],
                                leave_action=lambda: self.open_item_menu(index)
                            ))

                        item_action_options.append(Option(
                            label="Stats",
                            action=open_item_stats_menu,
                            condition=lambda: True
                        ))

                        self.enter_menu(menu=Menu(
                            options=[item_action_options],
                            title=[lambda: f"{item.name} Actions"],
                            leave_action=lambda: self.open_item_menu(index)
                        ))

                    return item_action_menu

                item_menu_options.append(Option(
                    label= f"{item.name}({item.durability})" if item.type == 'weapon' else f"{item.name}",
                    action= open_item_action_menu(),
                    condition= lambda: True
                ))

            self.enter_menu(menu=Menu(
                options=[item_menu_options],
                title=[lambda: "Item Menu"],
                option_index=option_index,
                leave_action=exit_menu
            ))

    def open_unit_menu(self, option_index=0):
        selectedCat = self.get_selected_cat()

        def exit_menu():
            self.state = 'map'
            self.cancel_cat_select()

        def check_house_condition():
            house = self.cat_is_on_house()
            if not selectedCat:
                return False
            if selectedCat and selectedCat.exhausted:
                return False
            if not house:
                return False
            if house.can_visit():
                return True
            return False
        
        def can_move():
            return selectedCat is not None and not selectedCat.moved and not selectedCat.exhausted

        def move_action():
            self.state = 'map'

        def wait_action():
            if selectedCat:
                selectedCat.set_exhausted(True)
            self.cancel_cat_select()
            self.state = 'map'

        def fight_action():
            def weapon_in_range(weapon):
                for enemy in self.level.enemies:
                    dx = abs(enemy.position.x - selectedCat.position.x)
                    dy = abs(enemy.position.y - selectedCat.position.y)
                    if (dx + dy) in weapon.get_range():
                        return True
                return False

            validWeapons = [
                (item, i)
                for i, item in enumerate(selectedCat.items)
                if item.type == 'weapon'
                and item.can_use(selectedCat.classType)
                and weapon_in_range(item)
            ]

            self.enter_menu(menu=Menu(
                options=[[
                    Option(
                        label= f"{item.name}",
                        action= lambda: (selectedCat.equip_item(i), self.set_state('enemy-select')),
                        condition= lambda: True
                    ) for item, i in validWeapons
                ]],
                title=[lambda: f"Pick Weapon"],
                leave_action=exit_menu
            ))


        def seize_action():
            if selectedCat:
                selectedCat.set_exhausted(True)
                selectedCat.set_moved(True)
            self.cancel_cat_select()
            self.state = 'map'
            GameState.load_next_level(self)

        def visit_house():
            house = self.cat_is_on_house()
            selCat = self.get_selected_cat()
            houseDialogs = house.get_dialogs()
            for dialog in houseDialogs:
                self.add_dialog(dialog)
            selCat.set_exhausted(True)
            selCat.set_moved(True)
            exit_menu()

        def can_attack():
            cat = self.get_selected_cat()
            if not cat:
                return False
            if cat.exhausted:
                return False
            for enemy in self.level.enemies:
                dx = abs(enemy.position.x - cat.position.x)
                dy = abs(enemy.position.y - cat.position.y)
                for catWeapon in [item for item in cat.items if item.type == 'weapon' and item.can_use(cat.classType)]:
                    if catWeapon and dx + dy in catWeapon.get_range():
                        return True
            return False
        
        def check_shop_condition():
            shop = self.cat_is_on_shop()
            selCat = self.get_selected_cat()
            if selCat and selectedCat.exhausted:
                return False
            return shop is not None
        
        def open_shop_action():
            shop = self.cat_is_on_shop()
            if shop:
                self.open_shop_menu(shop)
                self.needsUpdate = True

        def can_talk():
            for conversation in self.level.conversations:       
                if not selectedCat:
                    return False
                conversationNames = [conversation.nameOne, conversation.nameTwo]
                unitsInRange = self.units_in_range(selectedCat.position, 1)
                if len(unitsInRange) == 0:
                    return False
                firstFound = any(conversationNames[0] == unit.name for unit in unitsInRange)
                secondFound = any(conversationNames[1] == unit.name for unit in unitsInRange)
                if firstFound and secondFound and conversation.condition():
                    return True
            return False
        
        def talk_action():
            for conversation in self.level.conversations:
                conversationNames = [conversation.nameOne, conversation.nameTwo]
                unitsInRange = self.units_in_range(self.level.selectorPosition, 1)
                firstFound = [conversationNames[0] == unit.name for unit in unitsInRange]
                secondFound = [conversationNames[1] == unit.name for unit in unitsInRange]
                if firstFound and secondFound:
                    for dialog in conversation.dialogs:
                        self.add_dialog(dialog)
                    # remove conversation so it can't be triggered again
                    self.level.conversations.remove(conversation)
                    selectedCat.set_exhausted(True)
                    exit_menu()
                    break

        def can_press():
            cat = self.get_selected_cat()
            if not cat or cat.exhausted:
                return False
            for button in self.level.buttons:
                if button.position == cat.position and button.can_press():
                    return True
            return False

        def press_action():
            cat = self.get_selected_cat()
            if not cat:
                return
            for button in self.level.buttons:
                if button.position == cat.position and button.can_press():
                    button.press()
                    cat.set_exhausted(True)
                    cat.set_moved(True)
                    self.add_dialog(Dialog(
                        left_cats=[cat],
                        currentlyTalking=cat.name,
                        lines=["*pressed the", "button*"],
                    ))
                    selectedCat.set_exhausted(True)
                    exit_menu()
                    break

        menu_title = f"{selectedCat.name} hp:{selectedCat.hp}" if selectedCat else "Unit Menu"
        self.enter_menu(menu = Menu(
            options=[[
                Option(
                    label= "Seize",
                    action= seize_action,
                    condition= lambda: selectedCat and selectedCat.position == self.level.seizePosition
                ), Option(
                    label= "Fight",
                    action= fight_action,
                    condition= can_attack
                ), Option(
                    label="Press",
                    action= press_action,
                    condition= can_press
                ), Option(
                    label= "Move",
                    action= move_action,
                    condition= can_move
                ), Option(
                    label= "Wait",
                    action= wait_action,
                    condition= lambda: self.get_selected_cat() is not None and not self.get_selected_cat().exhausted
                ), Option(
                    label= "Talk",
                    action= talk_action,
                    condition= can_talk
                ), Option(
                    label= "Visit",
                    action= visit_house,
                    condition= check_house_condition
                ), Option(
                    label= "Shop",
                    action= open_shop_action,
                    condition= check_shop_condition
                ), Option(
                    label= "Items",
                    action= self.open_item_menu,
                    condition= lambda: selectedCat is not None and len(selectedCat.items) > 0
                ), Option(
                    label= "Stats",
                    action= lambda: self.open_stats(selectedCat),
                    condition= lambda: self.selectedCatId is not None
                ), Option(
                    label= "End Turn",
                    action= self.end_turn,
                    condition= lambda: True
                )
            ]],
            title=[lambda: menu_title],
            option_index=option_index,
            leave_action=exit_menu
        ))

    def open_stats(self, unit: Cat | None):
        if not unit:
            self.state = 'map'
            return

        def close_stats():
            self.state = 'map'
            self.cancel_cat_select()

        stats_options = [
            Option(label=f"lv{unit.level} {unit.classType}", action=lambda: None),
            Option(label=f"hp: {unit.hp}/{unit.stats.max_hp}", action=lambda: None),
            Option(label=f"attk: {unit.stats.attack}", action=lambda: None),
            Option(label=f"defn: {unit.stats.defense}", action=lambda: None),
            Option(label=f"speed: {unit.stats.speed}", action=lambda: None),
            Option(label=f"luck: {unit.stats.luck}", action=lambda: None),
            Option(label=f"rang: {unit.stats.range}", action=lambda: None),
            Option(label=f"xp: {unit.exp}/{unit.next_level_exp}", action=lambda: None),
            Option(label="Back", action=close_stats),
        ]

        growthRate_options = [
            Option(label=f"atk: {unit.growthRates.attack}", action=lambda: None),
            Option(label=f"def: {unit.growthRates.defense}", action=lambda: None),
            Option(label=f"hp: {unit.growthRates.max_hp}", action=lambda: None),
            Option(label=f"spd: {unit.growthRates.speed}", action=lambda: None),
            Option(label=f"lck: {unit.growthRates.luck}", action=lambda: None),
            Option(label=f"rng: {unit.growthRates.range}", action=lambda: None),
            Option(label="Back", action=close_stats),
        ]

        WeaponExp_options = []

        for label, value in [
            ("sword", unit.weaponExp.sword),
            ("repeatr", unit.weaponExp.repeater),
            ("longbow", unit.weaponExp.longbow),
            ("bow", unit.weaponExp.bow),
            ("lghtng", unit.weaponExp.lightning),
            ("water", unit.weaponExp.water),
            ("earth", unit.weaponExp.earth),
            ("mace", unit.weaponExp.mace),
            ("spear", unit.weaponExp.spear),
        ]:
            if value != -1:
                WeaponExp_options.append(
                    Option(label=f"{label}: {value}", action=lambda: None)
                )

        WeaponExp_options.append(Option(label="Back", action=close_stats))
        item_options: list[Option] = []
        for item in unit.items:
            item_options.append(Option(label=f"{item.name}({item.durability})" if item.type == 'weapon' else f"{item.name}", action=lambda: None))
        if len(item_options) == 0:
            item_options.append(Option(label="none", action=lambda: None))
        item_options.append(Option(label="Back", action=close_stats))

        stats_menu = Menu(
            options=[stats_options, item_options, WeaponExp_options, growthRate_options],
            title=[lambda: unit.name, lambda: f"{unit.name} Items", lambda: f"{unit.name} WeapXp", lambda: f"{unit.name} Growth"],
            option_index=0,
            leave_action=close_stats
        )
        
        self.enter_menu(stats_menu)

    def is_occupied(self, position: Position):
        return any(cat.position == position for cat in self.party + self.level.enemies)
