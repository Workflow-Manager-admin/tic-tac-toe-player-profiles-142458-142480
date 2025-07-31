import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import models
from .serializers import (
    RegisterSerializer, LoginSerializer, StartGameSerializer, MakeMoveSerializer
)

# Helper: Build empty game board
def create_empty_board():
    return [['' for _ in range(3)] for _ in range(3)]

# Helper: Check win
def check_winner(board):
    # Rows
    for row in board:
        if row[0] and row[0] == row[1] == row[2]:
            return row[0]
    # Columns
    for c in range(3):
        if board[0][c] and board[0][c] == board[1][c] == board[2][c]:
            return board[0][c]
    # Diagonals
    if board[0][0] and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return None

# Helper: Check draw
def check_draw(board):
    return all(cell for row in board for cell in row)

# PUBLIC_INTERFACE
@api_view(['POST'])
def register(request):
    """
    Registers a new user.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    if models.find_user_by_username(username):
        return Response({"error": "Username already exists."}, status=409)
    user_obj = {"username": username, "password": password, "wins": [], "losses": [], "draws": []}
    models.create_user(user_obj)
    return Response({"message": "User registered successfully."}, status=201)

# PUBLIC_INTERFACE
@api_view(['POST'])
def login(request):
    """
    Authenticates an existing user.
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    user = models.find_user_by_username(username)
    if not user or not models.verify_password(user, password):
        return Response({"error": "Invalid username or password."}, status=401)
    # For demo simplicity, just return user_id as a session token (not secure).
    return Response({"message": "Login successful.", "user_id": str(user["_id"])})

# PUBLIC_INTERFACE
@api_view(['POST'])
def start_game(request):
    """
    Starts a new PvP game with opponent.
    """
    serializer = StartGameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    auth_id = request.headers.get("X-User-Id")
    if not auth_id:
        return Response({"error": "Authentication required (missing X-User-Id header)."}, status=401)
    user = models.find_user_by_id(auth_id)
    if not user:
        return Response({"error": "Invalid user."}, status=401)
    opponent_username = serializer.validated_data["opponent_username"]
    if user["username"] == opponent_username:
        return Response({"error": "Cannot start a game with yourself."}, status=400)
    opp = models.find_user_by_username(opponent_username)
    if not opp:
        return Response({"error": "Opponent not found."}, status=404)
    # Let creator always be X, opponent O
    board = create_empty_board()
    now = datetime.datetime.utcnow()
    game = {
        "player_x": str(user["_id"]),
        "player_o": str(opp["_id"]),
        "board": board,
        "moves": [],
        "status": "ongoing",
        "current_turn": str(user["_id"]),
        "created_at": now,
        "result": {},
    }
    res = models.create_game(game)
    return Response({"game_id": str(res.inserted_id)}, status=201)

# PUBLIC_INTERFACE
@api_view(['POST'])
def make_move(request, game_id):
    """
    Player makes a move in an existing game.
    """
    serializer = MakeMoveSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    auth_id = request.headers.get("X-User-Id")
    if not auth_id:
        return Response({"error": "Authentication required (missing X-User-Id header)."}, status=401)
    user_id = auth_id
    game = models.find_game_by_id(game_id)
    if not game:
        return Response({"error": "Game not found."}, status=404)
    if game["status"] != "ongoing":
        return Response({"error": f"Game already finished: {game.get('status', '')}"}, status=400)
    # Only X or O can move, must be their turn
    if user_id not in [game["player_x"], game["player_o"]]:
        return Response({"error": "You are not a player in this game."}, status=403)
    expected_symbol = "X" if user_id == game["player_x"] else "O"
    if expected_symbol != serializer.validated_data["symbol"]:
        return Response({"error": "You are not allowed to play as this symbol."}, status=403)
    if user_id != game.get("current_turn"):
        return Response({"error": "Not your turn."}, status=403)
    row = serializer.validated_data["row"]
    col = serializer.validated_data["col"]
    board = game["board"]
    if not (0 <= row < 3 and 0 <= col < 3):
        return Response({"error": "Move out of bounds."}, status=400)
    if board[row][col]:
        return Response({"error": "Cell already occupied."}, status=400)
    symbol = serializer.validated_data["symbol"]
    board[row][col] = symbol
    # Record move
    moves = game.get("moves", [])
    moves.append({"row": row, "col": col, "symbol": symbol, "user_id": user_id, "ts": datetime.datetime.utcnow()})
    # Winner check
    winner = check_winner(board)
    is_draw = check_draw(board) and not winner
    new_status = "ongoing"
    update_fields = {
        "board": board,
        "moves": moves,
    }
    if winner:
        new_status = "finished"
        update_fields["status"] = new_status
        update_fields["result"] = {"winner": user_id, "symbol": symbol}
        # Update player records (simple)
        player_x_id = game["player_x"]
        player_o_id = game["player_o"]
        if winner == "X":
            win_user, lose_user = player_x_id, player_o_id
        else:
            win_user, lose_user = player_o_id, player_x_id
        db = models.get_db()
        db[models.USER_COLLECTION].update_one({"_id": models.ObjectId(win_user)}, {"$push": {"wins": str(game["_id"])}}, upsert=True)
        db[models.USER_COLLECTION].update_one({"_id": models.ObjectId(lose_user)}, {"$push": {"losses": str(game["_id"])}}, upsert=True)
    elif is_draw:
        new_status = "finished"
        update_fields["status"] = new_status
        update_fields["result"] = {"draw": True}
        player_x_id = game["player_x"]
        player_o_id = game["player_o"]
        db = models.get_db()
        db[models.USER_COLLECTION].update_one({"_id": models.ObjectId(player_x_id)}, {"$push": {"draws": str(game["_id"])}}, upsert=True)
        db[models.USER_COLLECTION].update_one({"_id": models.ObjectId(player_o_id)}, {"$push": {"draws": str(game["_id"])}}, upsert=True)
    else:
        # Next turn to other player
        next_turn = game["player_o"] if user_id == game["player_x"] else game["player_x"]
        update_fields["current_turn"] = next_turn
    models.update_game(game_id, update_fields)
    return Response({"message": "Move successful.", "status": new_status})

# PUBLIC_INTERFACE
@api_view(['GET'])
def game_state(request, game_id):
    """
    Returns the board and state for a game.
    """
    game = models.find_game_by_id(game_id)
    if not game:
        return Response({"error": "Game not found."}, status=404)
    resp = {
        "game_id": str(game["_id"]),
        "player_x": str(game["player_x"]),
        "player_o": str(game["player_o"]),
        "board": game["board"],
        "current_turn": game.get("current_turn", ""),
        "status": game.get("status", "ongoing"),
        "winner": game.get("result", {}).get("winner", ""),
        "draw": bool(game.get("result", {}).get("draw")),
    }
    return Response(resp)

# PUBLIC_INTERFACE
@api_view(['GET'])
def leaderboard(request):
    """
    Returns sorted leaderboard (top 10).
    """
    leaders = models.get_leaderboard(limit=10)
    return Response(leaders)

# PUBLIC_INTERFACE
@api_view(['GET'])
def user_games(request, user_id):
    """
    Returns all games played by a given user.
    """
    games = models.get_user_game_history(user_id)
    response_data = []
    for g in games:
        if str(g["player_x"]) == user_id:
            opponent_id = g["player_o"]
        else:
            opponent_id = g["player_x"]
        result = "draw" if g.get("result", {}).get("draw") else \
            ("win" if (g.get("result", {}).get("winner") == user_id) else "loss")
        response_data.append({
            "game_id": str(g["_id"]),
            "opponent": opponent_id,
            "result": result,
            "created_at": g.get("created_at"),
        })
    return Response(response_data)

@api_view(['GET'])
def health(request):
    return Response({"message": "Server is up!"})
