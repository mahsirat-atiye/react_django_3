from sport.models import FootballTeam, FootballPlayer, FootballGame, FootballLeague, BasketballGame

import logging

from sport.views.general_views import *


def football_teams(request):
    teams = FootballTeam.objects.all()

    context = {
        'teams': teams
    }
    return render(request, 'sport/football/football_teams.html', context)


def football_team_detail_view(request, team_id):
    news = News.objects.all().order_by('-publish_date')

    team = get_object_or_404(FootballTeam, pk=team_id)
    team_in_games = team.footballteaminfootballgame_set.all().order_by('team_score')

    games = []
    for tg in team_in_games:
        games.append(tg.game)
    related_news = get_related_news_by_all_criteria(news, team.name)

    if request.POST:
        if request.POST["part"] == 'filter_news':
            if request.POST['choice'] == 'tag':
                related_news = get_related_news_by_tag(news, team.name)
            elif request.POST['choice'] == 'title':
                related_news = get_related_news_by_title(news, team.name)
            else:
                related_news = get_related_news_by_text(news, team.name)
        elif request.POST["part"] == 'winning_losing':
            games = filter_games_by_winning_loosing(team_in_games, request.POST["choice"])
        elif request.POST["part"] == 'opponent_team':
            games = filter_games_by_opponent(games, team=team, text=request.POST["opponent_team"])
        elif request.POST['part'] == 'follow':
            team.followers.add(request.user)
            logger = logging.getLogger(__name__)
            logger.info('با موفقیت از این تیم پیروی شد!')

    context = {
        'team': team,
        'related_news': related_news,
        'games': games
    }

    return render(request, 'sport/team_detail.html', context)


def football_player_detail_view(request, player_id):
    news = News.objects.all().order_by('-publish_date')
    player = get_object_or_404(FootballPlayer, pk=player_id)
    related_news = get_related_news_by_all_criteria(news, player.first_name, player.last_name)
    if request.POST and request.POST['part'] == 'for_season':
        # todo
        # مفهوم فصل در فوتبال با علی چک شود
        season = request.POST['season']
        season = int(season)
        x = datetime.datetime(season, 1, 1)
        y = datetime.datetime(season + 1, 1, 1)
        events = player.footballevent_set.all().filter(exact_time__lte=y).filter(exact_time__gte=x)
    else:
        events = player.footballevent_set.all()

    details = get_details_football(events)

    if request.POST and request.POST['part'] == 'filter_news':
        if request.POST['choice'] == 'tag':
            related_news = get_related_news_by_tag(news, player.first_name, player.last_name)

        elif request.POST['choice'] == 'title':
            related_news = get_related_news_by_title(news, player.first_name, player.last_name)
        else:
            related_news = get_related_news_by_text(news, player.first_name, player.last_name)
    if request.POST and request.POST['part'] == 'follow':
        player.followers.add(request.user)
        logger = logging.getLogger(__name__)
        logger.info('با موفقیت از این بازیکن پیروی شد!')
    context = {
        'player': player,
        'related_news': related_news,
        'details': details

    }
    # context.update(details)

    return render(request, 'sport/football/football_player_detail.html', context)


def football_game_detail_view(request, game_id):
    game = get_object_or_404(FootballGame, pk=game_id)
    teams = game.footballteaminfootballgame_set.all()
    team = teams[0].team
    events = get_events_by_game_and_team(game, team)
    first_team_details = get_details_football(events)

    team = teams[1].team

    events = get_events_by_game_and_team(game, team)
    second_team_details = get_details_football(events)

    news = News.objects.all().filter(publish_date__lt=game.date).order_by('-publish_date')
    news_before = get_related_news_to_game(news, teams[0].team.name, teams[1].team.name)

    news = News.objects.all().filter(publish_date__gte=game.date).order_by('-publish_date')
    news_after = get_related_news_to_game(news, teams[0].team.name, teams[1].team.name)

    first_team_players_in_game = []
    second_team_players_in_game = []
    for pg in game.footballplayerinfootballgame_set.all():
        if pg.player.team == teams[0].team:
            first_team_players_in_game.append(pg)
        else:
            second_team_players_in_game.append(pg)

    context = {
        'game': game,
        'first_team_details': first_team_details,
        'second_team_details': second_team_details,
        'teams': teams,
        'news_before': news_before,
        'news_after': news_after,
        'first_team_players_in_game': first_team_players_in_game,
        'second_team_players_in_game': second_team_players_in_game

    }
    return render(request, 'sport/football/football_game_detail.html', context)


def football_leagues(request):
    current_year = timezone.now().year
    current_year = int(current_year)

    current_leagues = FootballLeague.objects.filter(year__gte=current_year)
    archive_leagues = FootballLeague.objects.filter(year__lt=current_year).order_by('-year')

    if request.POST:
        current_leagues = filter_leagues_by_text(current_leagues, request.POST["part_of_league"])
        archive_leagues = filter_leagues_by_text(archive_leagues, request.POST['part_of_league'])

    context = {
        'current_leagues': current_leagues,
        'archive_leagues': archive_leagues
    }
    return render(request, 'sport/football/football_leagues.html', context)


def football_league_detail(request, league_id):
    league = get_object_or_404(FootballLeague, pk=league_id)

    # for weeks:
    games_separated_by_weeks = separate_by_week(league)

    details_of_games_separated_by_weeks = []
    for gw in games_separated_by_weeks:
        details_of_games_of_current_week = []
        for g in gw:
            details = get_details_of_game_football(g)
            details_of_games_of_current_week.append(details)
        details_of_games_separated_by_weeks.append(details_of_games_of_current_week)

    context = {
        'league': league,
        'details_of_games_separated_by_weeks': details_of_games_separated_by_weeks
    }
    return render(request, 'sport/football/football_league_detail.html', context)


# -------------------------------------------------------------------------------------
def get_details_football(events):
    total_G = 0
    total_PG = 0
    total_YC = 0
    total_RC = 0
    total_E = 0
    total_P = 0
    total_CH = 0
    total_CO = 0
    total_SG = 0

    for e in events:
        if e.event_type == 'G':
            total_G += 1
        elif e.event_type == 'PG':
            total_PG += 1
        elif e.event_type == 'YC':
            total_YC += 1
        elif e.event_type == 'RC':
            total_RC += 1
        elif e.event_type == 'E':
            total_E += 1
        elif e.event_type == 'P':
            total_P += 1
        elif e.event_type == 'CH':
            total_CH += 1
        elif e.event_type == 'CO':
            total_CO += 1
        elif e.event_type == 'SG':
            total_SG += 1
    return {'total_G': total_G,
            'total_PG': total_PG,
            'total_YC': total_YC,
            'total_RC': total_RC,
            'total_E': total_E,
            'total_P': total_P,
            'total_CH': total_CH,
            'total_CO': total_CO,
            'total_SG': total_SG}


def get_details_of_game_football(game):
    teams = game.footballteaminfootballgame_set.all()
    team = teams[0].team
    events = get_events_by_game_and_team(game, team)
    first_team_details = get_details_football(events)

    team = teams[1].team

    events = get_events_by_game_and_team(game, team)
    second_team_details = get_details_football(events)

    details = {
        'game': game,
        'teams': teams,
        'first_team_details': first_team_details,
        'second_team_details': second_team_details
    }
    return details
