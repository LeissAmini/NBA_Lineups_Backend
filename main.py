from fastapi.responses import JSONResponse
from fastapi import FastAPI
from nba_api.live.nba.endpoints import scoreboard, boxscore
from dateutil import parser

app = FastAPI()

@app.get("/")
def get_today_games():
    # Fetch live scoreboard data
    try:
        
        scoreboard_data = scoreboard.ScoreBoard()
        games_data = scoreboard_data.get_dict().get("scoreboard", {}).get("games", [])
    except Exception as e:
        print(f"Error fetching scoreboard data: {e}")
        return JSONResponse(status_code=503, content={"error": "Could not fetch NBA scoreboard data"})

    formatted_games = []
    for game in games_data:
        game_id = game["gameId"]

        # Convert tip-off time from ET to readable format
        tipoff_time_utc = game.get("gameEt")
        if not tipoff_time_utc:
            continue

        try:
            parsed_time = parser.parse(tipoff_time_utc)  # Automatically handles timezones
            tipoff_time = parsed_time.strftime("%I:%M %p")  # Convert to readable format
            game_date = parsed_time.strftime("%B %d, %Y")  # Format date
        except Exception as e:
            print(f"Error parsing tip-off time: {e}")
            tipoff_time = "Unknown"
            game_date = "Unknown"

        home_team = game["homeTeam"]
        away_team = game["awayTeam"]

        try:
            boxscore_data = boxscore.BoxScore(game_id).get_dict().get("game", {})

            home_players = [
                {"name": player["name"], "position": player["position"]}
                for player in boxscore_data.get("homeTeam", {}).get("players", [])
                if player.get("position")  # Only add players with a position
            ]
            away_players = [
                {"name": player["name"], "position": player["position"]}
                for player in boxscore_data.get("awayTeam", {}).get("players", [])
                if player.get("position")  # Only add players with a position
            ]
        except Exception as e:
            print(f"Error fetching boxscore for game {game_id}: {e}")
            home_players = []
            away_players = []

        # Add Placeholder if No Starters Available
        if not home_players:
            home_players = [{"name": "Lineup not available yet", "position": "-"}]
        if not away_players:
            away_players = [{"name": "Lineup not available yet", "position": "-"}]

        formatted_games.append({
            "gameInfo": {
                "tipOffTime": tipoff_time,
                "date": game_date
            },
            "teams": {
                "home": {
                    "name": f"{home_team['teamCity']} {home_team['teamName']}",
                    "record": f"{home_team['wins']}-{home_team['losses']}",
                    "players": home_players
                },
                "away": {
                    "name": f"{away_team['teamCity']} {away_team['teamName']}",
                    "record": f"{away_team['wins']}-{away_team['losses']}",
                    "players": away_players
                }
            }
        })

    return JSONResponse(content={"games": formatted_games})
