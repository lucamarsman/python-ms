from flask import Flask, jsonify, request
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import LeagueDashPlayerStats, LeagueDashTeamStats, LeagueGameFinder, BoxScoreTraditionalV2, LeagueStandingsV3, CommonPlayerInfo, LeagueGameFinder, ScoreboardV2
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.library.parameters import LeagueID
from datetime import datetime

app = Flask(__name__)


# FOR FETCHING TEAMS
@app.route('/teams', methods=['GET'])
def get_teams():
    try:
        all_teams = teams.get_teams()
        return jsonify(all_teams), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# FOR FETCHING PLAYERS
@app.route('/players', methods=['GET'])
def get_players():
    try:
        team_id = request.args.get('teamId')
        player_name = request.args.get('playerName')
        all_players = players.get_active_players()

        # Filter players by team ID or name if provided
        filtered_players = all_players
        if team_id:
            filtered_players = [p for p in filtered_players if str(p.get('team_id')) == team_id]
        if player_name:
            filtered_players = [p for p in filtered_players if player_name.lower() in p.get('full_name', '').lower()]

        return jsonify(filtered_players), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#FOR FETCHING BASIC PLAYER INFO BY PLAYERID
@app.route('/player-info', methods=['GET'])
def get_player_info():
    try:
        player_id = request.args.get('PlayerId')

        player_info = CommonPlayerInfo(player_id=player_id).get_normalized_dict()

        return jsonify(player_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# FOR FETCHING PLAYER SEASON STATS
@app.route('/stats/players', methods=['GET'])
def get_season_stats_player():
    try:
        season = request.args.get('Season', '2024-25')  # Default to the current season
        per_mode = request.args.get('PerMode')  # Default to PerGame stats
        season_type = request.args.get('SeasonType', 'Regular Season')  # Default to regular season

        # Fetch player stats for the specified season
        player_stats = LeagueDashPlayerStats(
            season=season,
            per_mode_detailed=per_mode,
            season_type_all_star=season_type
        )

        stats = player_stats.get_normalized_dict()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# FOR FETCHING TEAM SEASON STATS
@app.route('/stats/teams', methods=['GET'])
def get_season_stats_team():
    try:
        season = request.args.get('Season', '2024-25')  # Default to the current season
        per_mode = request.args.get('PerMode')  # Default to PerGame stats  Totals
        season_type = request.args.get('SeasonType', 'Regular Season')  # Default to regular season

        # Fetch player stats for the specified season
        player_stats = LeagueDashTeamStats(
            season=season,
            per_mode_detailed=per_mode,
            season_type_all_star=season_type
        )

        stats = player_stats.get_normalized_dict()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#FOR GETTING LIVE GAME DATA
@app.route('/live-games', methods=['GET'])
def get_live_games():
    try:
        liveGames = scoreboard.ScoreBoard().games.get_dict()
        return jsonify(liveGames), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#FOR GETTING BOX SCORE FOR A GAME
@app.route('/boxscore', methods=['GET'])
def get_boxscore():
    try:
        game_id = request.args.get('gameId')
        if not game_id:
            return jsonify({"error": "gameId parameter is required"}), 400

        # Fetch the box score
        box_score = BoxScoreTraditionalV2(game_id=game_id)
        data = box_score.get_normalized_dict()

        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#FOR GETTING CONFERENCE STANDINGS
#EXAMPLE: /standings?LeagueId=00&Season=2024-25&SeasonType=Regular%20Season
@app.route('/standings', methods=['GET'])
def get_standings():
    try:
        league_id = request.args.get('LeagueId')
        season = request.args.get('Season')
        season_type = request.args.get('SeasonType')
        standings = LeagueStandingsV3(
            league_id = league_id,
            season = season,
            season_type = season_type
        )
        standings_data = standings.get_normalized_dict()
        return jsonify(standings_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#FOR GETTING GAME SCHEDULE FOR SPECFIC TEAM/SEASON/DATE RANGE
@app.route('/schedule', methods=['GET'])
def get_schedule():
    try:
        season = request.args.get('Season', '2024-25')  # Default to current season
        league_id = request.args.get("LeagueId", LeagueID.default)
        team_id = request.args.get('TeamId')  # Optional: Team ID to filter
        start_date = request.args.get('StartDate')  # Optional: Start date (YYYY-MM-DD)
        end_date = request.args.get('EndDate')  # Optional: End date (YYYY-MM-DD)

        game_finder = LeagueGameFinder(
            season_nullable=season,
            team_id_nullable=team_id,
            league_id_nullable = league_id
        )
        games = game_finder.get_data_frames()[0]

        # Filter games by date range if provided
        if start_date:
            games = games[games['GAME_DATE'] >= start_date]
        if end_date:
            games = games[games['GAME_DATE'] <= end_date]

        games_list = games.to_dict(orient='records')

        return jsonify(games_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#FOR FETCHING GAMES FOR A CERTAIN DATE
@app.route('/games', methods=['GET'])
def get_games():
    try:
        league_id = request.args.get('LeagueId', LeagueID.default)
        day_offset = int(request.args.get('DayOffset', 0))
        game_date = request.args.get('GameDate', datetime.now().strftime('%Y-%m-%d'))

        try:
            datetime.strptime(game_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        games = ScoreboardV2(
            league_id=league_id,
            day_offset=day_offset,
            game_date=game_date
        )
        games_data = games.get_normalized_dict()
        return jsonify(games_data), 200

    except Exception as e:
        app.logger.error(f"Error fetching games: {e}")
        return jsonify({"error": "An error occurred while fetching games data."}), 500

if __name__ == "__main__":
    app.run(port=5000)
