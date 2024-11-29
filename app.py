from flask import Flask, jsonify, request
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import LeagueDashPlayerStats, LeagueDashTeamStats, LeagueGameFinder, BoxScoreTraditionalV2, LeagueStandingsV3, CommonPlayerInfo, LeagueGameFinder, ScoreboardV2, commonallplayers, playerawards
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.library.parameters import LeagueID
from datetime import datetime

app = Flask(__name__)

@app.route('/seasons', methods=['GET'])
def get_seasons():
    try:
        from nba_api.stats.endpoints import commonteamyears
        # Fetch the team years data
        team_years = commonteamyears.CommonTeamYears()
        team_years_data = team_years.get_data_frames()[0]

        # Extract MIN_YEAR and MAX_YEAR columns
        min_years = [int(year) for year in team_years_data['MIN_YEAR'].unique()]
        max_years = [int(year) for year in team_years_data['MAX_YEAR'].unique()]

        # Generate all years between MIN_YEAR and MAX_YEAR
        all_years = set()
        for min_year, max_year in zip(min_years, max_years):
            all_years.update(range(min_year, max_year + 1))

        # Filter for seasons starting from 2010 onwards
        filtered_years = sorted([year for year in all_years if year >= 2010])

        # Convert to "YYYY-YY" format
        seasons = [f"{year}-{str(year + 1)[-2:]}" for year in filtered_years]

        return jsonify(seasons), 200
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500
       

# FOR FETCHING TEAMS
@app.route('/teams', methods=['GET'])
def get_teams():
    try:
        all_teams = teams.get_teams()
        return jsonify(all_teams), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/players', methods=['GET'])
def get_players():
    try:
        # Get the start and end year from request arguments, with defaults
        start_year = int(request.args.get('startYear', 2010))
        end_year = int(request.args.get('endYear', datetime.now().year))

        # Fetch all players for the latest season (end year)
        season_str = f"{end_year}-{str(end_year + 1)[-2:]}"
        players = commonallplayers.CommonAllPlayers(is_only_current_season=0, season=season_str).get_data_frames()[0]

        # Convert 'FROM_YEAR' and 'TO_YEAR' columns to integers
        players['FROM_YEAR'] = players['FROM_YEAR'].astype(int)
        players['TO_YEAR'] = players['TO_YEAR'].astype(int)

        # Filter players by debut and final year
        filtered_players = players[
            (players['FROM_YEAR'] <= end_year) & (players['TO_YEAR'] >= start_year)
        ]

        # Convert the filtered players to a dictionary for JSON response
        filtered_players_dict = filtered_players.to_dict(orient='records')

        return jsonify(filtered_players_dict), 200
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
    

#FOR FETCHING PLAYER AWARDS
@app.route('/player-awards', methods=['GET'])
def get_player_awards():
    try:
        player_id = request.args.get('PlayerId')
        awards = playerawards.PlayerAwards(player_id=player_id).get_data_frames()[0]

        player_awards = awards.to_dict(orient='records')
        
        return jsonify(player_awards), 200
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
        season = request.args.get('Season')  # Default to the current season
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
