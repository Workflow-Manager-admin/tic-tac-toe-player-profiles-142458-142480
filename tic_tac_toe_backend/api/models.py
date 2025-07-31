import os
from pymongo import MongoClient
from bson import ObjectId

# PUBLIC_INTERFACE
def get_mongo_client():
    """Returns a MongoDB client using environment variables."""
    mongo_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/")
    return MongoClient(mongo_url)

# PUBLIC_INTERFACE
def get_db():
    """Returns the database object for the configured MongoDB DB."""
    client = get_mongo_client()
    db_name = os.environ.get("MONGODB_DB", "tic_tac_toe")
    return client[db_name]


# COLLECTION NAMES
USER_COLLECTION = 'users'
GAME_COLLECTION = 'games'

# PUBLIC_INTERFACE
def find_user_by_username(username):
    """Find user by username in MongoDB."""
    db = get_db()
    return db[USER_COLLECTION].find_one({"username": username})

# PUBLIC_INTERFACE
def find_user_by_id(user_id):
    """Find user by user_id in MongoDB."""
    db = get_db()
    return db[USER_COLLECTION].find_one({"_id": ObjectId(user_id)})

# PUBLIC_INTERFACE
def create_user(user_obj):
    """Insert a new user document."""
    db = get_db()
    return db[USER_COLLECTION].insert_one(user_obj)

# PUBLIC_INTERFACE
def create_game(game_obj):
    """Insert a new game document."""
    db = get_db()
    return db[GAME_COLLECTION].insert_one(game_obj)

# PUBLIC_INTERFACE
def find_game_by_id(game_id):
    """Find a game by its ObjectId."""
    db = get_db()
    return db[GAME_COLLECTION].find_one({"_id": ObjectId(game_id)})

# PUBLIC_INTERFACE
def update_game(game_id, update_dict):
    """Update a game's fields."""
    db = get_db()
    return db[GAME_COLLECTION].update_one({"_id": ObjectId(game_id)}, {"$set": update_dict})

# PUBLIC_INTERFACE
def get_leaderboard(limit=10):
    """
    Return players with top win counts, along with their username/wins/losses/draws.
    Orders by wins descending.
    """
    db = get_db()
    pipeline = [
        {"$addFields": {
            "win_count": {"$size": {"$ifNull": ["$wins", []]}},
            "loss_count": {"$size": {"$ifNull": ["$losses", []]}},
            "draw_count": {"$size": {"$ifNull": ["$draws", []]}},
        }},
        {"$sort": {"win_count": -1, "username": 1}},
        {"$limit": limit},
        {"$project": {
            "username": 1,
            "win_count": 1,
            "loss_count": 1,
            "draw_count": 1,
        }},
    ]
    return list(db[USER_COLLECTION].aggregate(pipeline))

# PUBLIC_INTERFACE
def get_user_game_history(user_id):
    """
    Returns a list of games for the given user, sorted by date.
    """
    db = get_db()
    return list(
        db[GAME_COLLECTION].find({
            "$or": [
                {"player_x": user_id},
                {"player_o": user_id}
            ]
        }).sort([("created_at", -1)])
    )

# PUBLIC_INTERFACE
def verify_password(user_obj, password):
    """Checks password for user document."""
    # For production, use hashed pw, not plain text! Here for demo.
    return user_obj and user_obj.get("password") == password

# PUBLIC_INTERFACE
def record_game_result(game_id, winner_id=None, draw=False):
    """Update game result (winner or draw) in db."""
    game = find_game_by_id(game_id)
    if not game:
        return
    # Set result fields
    result = {"result": {}}
    if draw:
        result["result"]["draw"] = True
    elif winner_id:
        result["result"]["winner"] = winner_id
    update_game(game_id, result)
