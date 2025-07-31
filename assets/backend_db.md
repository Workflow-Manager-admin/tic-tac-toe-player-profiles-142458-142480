# Backend/MongoDB Configuration for Tic-Tac-Toe Backend

## Required Environment Variables

Set the following environment variables in your deployment environment or .env file for Django settings to enable MongoDB connectivity:

- `MONGODB_URL`: The MongoDB connection URI (e.g., mongodb://user:password@host:port/db)
- `MONGODB_DB`: The database name (e.g., tic_tac_toe)

## Usage

- User, game, and leaderboard data is stored in MongoDB via pymongo.
- All Django REST endpoints access and update this MongoDB database using the settings above.

## REST Endpoints Provided

- `POST /api/register`
- `POST /api/login`
- `POST /api/games/start`
- `POST /api/games/{game_id}/move`
- `GET /api/games/{game_id}`
- `GET /api/leaderboard`
- `GET /api/users/{user_id}/games`

## Authentication

- All routes except registration and login require clients to add HTTP header: `X-User-Id` with the user id (as a session token). 
- For production, use a JWT or session mechanism; this is a demonstration only.
