import datetime

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import generic

from sport.models import News, FootballTeam, FootballPlayer, FootballGame, FootballLeague, BasketballGame
from django.utils import timezone
import logging


#
# class RecentGeneralNews(generic.ListView):
#     template_name = 'sport/general_home_page.html'
#     context_object_name = 'recent_news'
#
#     def get_queryset(self):
#         return News.objects.filter(publish_date__lte=timezone.now()).filter(type='F').order_by('-publish_date')[:10]


def recent_general_news(request):
    news = News.objects.filter(publish_date__lte=timezone.now()).filter(
        publish_date__gte=timezone.now() - datetime.timedelta(days=2)).order_by('-publish_date')

    teams = request.user.footballteam_set.all()  # for debug

    f1_ = request.user.footballteam_set.all()
    f2_ = request.user.footballplayer_set.all()
    f3_ = request.user.basketballteam_set.all()
    f4_ = request.user.basketballplayer_set.all()
    f1 = map(lambda x: x.name, f1_)
    f2 = map(lambda x: str(x), f2_)
    f3 = map(lambda x: str(x), f3_)
    f4 = map(lambda x: str(x), f4_)
    favorites = []
    favorites.extend(f1)
    favorites.extend(f2)
    favorites.extend(f3)
    favorites.extend(f4)

    # games:
    future_football_games = FootballGame.objects.filter(date__gt=timezone.now()).order_by('-date')[:10]
    future_basketball_games = BasketballGame.objects.filter(date__gt=timezone.now()).order_by('-date')[:10]

    football_games = FootballGame.objects.filter(date__lte=timezone.now()).order_by('-date')[:10]
    basketball_games = BasketballGame.objects.filter(date__lte=timezone.now()).order_by('-date')[:10]

    favorite_football_games = FootballGame.objects.filter(
        date__gt=timezone.now() - datetime.timedelta(days=1)).filter(
        date__lte=timezone.now() + datetime.timedelta(days=1)).order_by('-date')[:10]

    favorite_basketball_games = BasketballGame.objects.filter(
        date__gt=timezone.now() - datetime.timedelta(days=1)).filter(
        date__lte=timezone.now() + datetime.timedelta(days=1)).order_by('-date')[:10]

    # news
    favorite_news = get_related_news_by_all_criteria(news, *favorites)

    if request.POST:
        n = int(request.POST['number'])
        recent_news = News.objects.filter(publish_date__lte=timezone.now()).order_by('-publish_date')[:n]
    else:
        recent_news = News.objects.filter(publish_date__lte=timezone.now()).order_by('-publish_date')[:10]

    context = {
        'recent_news': recent_news,
        'favorite_news': favorite_news,
        'teams': teams,
        'future_football_games': future_football_games,
        'future_basketball_games': future_basketball_games,
        'football_games': football_games,
        'basketball_games': basketball_games,
        'favorite_football_games': favorite_football_games,
        'favorite_basketball_games': favorite_basketball_games

    }
    return render(request, 'sport/general_home_page.html', context)


def football_teams(request):
    teams = FootballTeam.objects.all()

    context = {
        'teams': teams
    }
    return render(request, 'sport/teams.html', context)


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

    return render(request, 'sport/football_team_detail.html', context)


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

    details = get_details(events)

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

    return render(request, 'sport/football_player_detail.html', context)


def football_game_detail_view(request, game_id):
    game = get_object_or_404(FootballGame, pk=game_id)
    teams = game.footballteaminfootballgame_set.all()
    team = teams[0].team
    events = get_events_by_game_and_team(game, team)
    first_team_details = get_details(events)

    team = teams[1].team

    events = get_events_by_game_and_team(game, team)
    second_team_details = get_details(events)

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
    return render(request, 'sport/football_game_detail.html', context)


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
    return render(request, 'sport/leagues.html', context)


def league_detail(request, league_id):
    league = get_object_or_404(FootballLeague, pk=league_id)

    # for weeks:
    games_separated_by_weeks = separate_by_week(league)

    details_of_games_separated_by_weeks = []
    for gw in games_separated_by_weeks:
        details_of_games_of_current_week = []
        for g in gw:
            details = get_details_of_game(g)
            details_of_games_of_current_week.append(details)
        details_of_games_separated_by_weeks.append(details_of_games_of_current_week)

    context = {
        'league': league,
        'details_of_games_separated_by_weeks': details_of_games_separated_by_weeks
    }
    return render(request, 'sport/football_league_detail.html', context)


#  ---------------------------------------------------------------------------------------
def get_details(events):
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


def get_events_by_game_and_team(game, team):
    events_ = game.footballevent_set.all()
    events = []
    for e in events_:
        if e.doer.team == team:
            events.append(e)
    return events


def get_related_news_by_all_criteria(news, *special_text):
    related_news = set([])
    for st in special_text:
        for n in news:
            for t in n.tag_set.all():
                if t.text.__contains__(st):
                    related_news.add(n)
            if n.title.__contains__(st):
                related_news.add(n)
            if n.text.__contains__(st):
                related_news.add(n)
    related_news = list(related_news)
    return related_news


def get_related_news_by_tag(news, *special_text):
    related_news = set([])
    for st in special_text:
        for n in news:
            for t in n.tag_set.all():
                if t.text.__contains__(st):
                    related_news.add(n)
    related_news = list(related_news)
    return related_news


def get_related_news_by_title(news, *special_text):
    related_news = set([])
    for st in special_text:
        for n in news:

            if n.title.__contains__(st):
                related_news.add(n)

    related_news = list(related_news)
    return related_news


def get_related_news_by_text(news, *special_text):
    related_news = set([])
    for st in special_text:
        for n in news:
            if n.text.__contains__(st):
                related_news.add(n)
    related_news = list(related_news)
    return related_news


def filter_games_by_opponent(games, team, text):
    filtered_games = []
    for g in games:
        teams_in_game = g.footballteaminfootballgame_set.all()
        if teams_in_game[0].team == team:
            opponent_name = teams_in_game[1].team.name

        else:
            opponent_name = teams_in_game[0].team.name

        if opponent_name.__contains__(text):
            filtered_games.append(g)

    return filtered_games


def filter_games_by_winning_loosing(team_in_games, situation_text):
    games = []
    for tg in team_in_games:
        if tg.situation == situation_text:
            games.append(tg.game)
    return games


def get_related_news_to_game(news, *team_names):
    related_news = set([])

    for n in news:
        if n.text.__contains__(team_names[0]) and n.text.__contains__(team_names[1]):
            related_news.add(n)
        if n.title.__contains__(team_names[0]) and n.text.__contains__(team_names[1]):
            related_news.add(n)
    related_news = list(related_news)
    return related_news


def filter_leagues_by_text(leagues, special_text):
    filtered_leagues = []
    for l in leagues:
        league_complete_name = str(l)
        if league_complete_name.__contains__(special_text):
            filtered_leagues.append(l)
    return filtered_leagues


def separate_by_week(league):
    games = league.footballgame_set.order_by('-date')
    last_game_date = games[0].date
    first_game_date = games.last().date

    # todo change it to persian # done ;))
    last_game_weekday = last_game_date.weekday()
    last_game_weekday += 2
    last_game_weekday %= 7

    last_interval = last_game_date - datetime.timedelta(days=last_game_weekday)
    last_week_games = league.footballgame_set.filter(
        date__gte=last_interval)
    first_game_weekday = first_game_date.weekday()

    first_game_weekday += 2
    first_game_weekday %= 7

    first_interval = first_game_date + datetime.timedelta(days=7 - first_game_weekday)
    first_week_games = league.footballgame_set.filter(
        date__lt=first_interval)

    games_by_weeks = [first_week_games]
    date = first_interval
    while date < last_interval:
        games_of_week = league.footballgame_set.filter(
            date__lte=date + datetime.timedelta(days=7)).filter(date__gt=date)
        games_by_weeks.append(games_of_week)
        date = date + datetime.timedelta(days=7)

    games_by_weeks.append(last_week_games)
    return games_by_weeks


def get_details_of_game(game):
    teams = game.footballteaminfootballgame_set.all()
    team = teams[0].team
    events = get_events_by_game_and_team(game, team)
    first_team_details = get_details(events)

    team = teams[1].team

    events = get_events_by_game_and_team(game, team)
    second_team_details = get_details(events)

    details = {
        'game': game,
        'teams': teams,
        'first_team_details': first_team_details,
        'second_team_details': second_team_details
    }
    return details
