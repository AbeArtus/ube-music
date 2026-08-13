# Shared callbacks between the main game loop and the act level modules.
# Kept tiny so it can be imported by CatsEmblem.py, ActOne.py and ActTwo.py
# without circular imports or extra memory cost.

_game_state = None

def set_game_state(gs):
	global _game_state
	_game_state = gs

def add_to_party(cat):
	_game_state.party.append(cat)

def update_bank(amount):
	_game_state.update_bank(amount)

def give_item(position, item):
	for p in _game_state.party:
		if p.position == position and len(p.items) < 4:
			p.items.append(item)
			return True
	return False

def can_give_item(position):
	for p in _game_state.party:
		if p.position == position and len(p.items) < 4:
			return True
	return False

def get_cat_at_pos(position):
	for p in _game_state.party:
		if p.position == position:
			return p
	return None

def get_selected_cat():
	return _game_state.get_selected_cat()

CALLBACKS = (add_to_party, update_bank, can_give_item, give_item, get_cat_at_pos, get_selected_cat)
