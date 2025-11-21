import json, os
from typing import Dict
from config import DATA_DIR

STATE = os.path.join(DATA_DIR, "state.json")

DEFAULT = {"stocks": [], "fx": [], "last_alerts": {}}

def load_state() -> Dict:
    if not os.path.exists(STATE):
        save_state(DEFAULT)
    with open(STATE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state: Dict):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def add_symbol(kind: str, sym: str) -> bool:
    s = load_state()
    arr = s[kind]
    sym = sym.upper()
    if sym not in arr:
        arr.append(sym)
        save_state(s)
        return True
    return False

def remove_symbol(kind: str, sym: str) -> bool:
    s = load_state()
    arr = s[kind]
    sym = sym.upper()
    if sym in arr:
        arr.remove(sym)
        save_state(s)
        return True
    return False


def save_stock_list(stock_list):
    """Save stock list to file and update in-memory cache"""
    try:
        stock_list_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stock_list.txt")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(stock_list_file), exist_ok=True)
        
        with open(stock_list_file, "w", encoding="utf-8") as f:
            f.write("# Stock symbols to monitor\n")
            f.write("# One symbol per line, comments start with #\n")
            for stock in stock_list:
                f.write(f"{stock.upper()}\n")
        
        # Update the in-memory cache
        import config
        config.STOCKS_TO_CHECK = list(stock_list)
        
        print(f"✅ Saved {len(stock_list)} stocks to {stock_list_file}")
        print(f"✅ Updated in-memory cache with {len(stock_list)} stocks")
        return True
        
    except Exception as e:
        print(f"❌ Error saving stock list: {e}")
        return False


def load_stock_list():
    """Load current stock list from config (cached) or reload from file if needed"""
    # Import here to avoid circular import
    from config import STOCKS_TO_CHECK
    import config
    
    # Check if we should reload from file
    try:
        stock_list_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stock_list.txt")
        
        if os.path.exists(stock_list_file):
            # For now, always return the current cache
            # The cache is updated by save_stock_list when changes are made
            return list(STOCKS_TO_CHECK)
        else:
            # File doesn't exist, return current cache
            return list(STOCKS_TO_CHECK)
            
    except Exception as e:
        print(f"⚠️ Error checking stock list file: {e}")
        return list(STOCKS_TO_CHECK)
