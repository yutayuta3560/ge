import datetime
import django.db.models.functions
from django.shortcuts import render, redirect, get_object_or_404
from .models import Balance, Location, Hotel, Game
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Sum
from django.contrib.auth.models import User
from django.http import JsonResponse
from datetime import datetime
from django.db.models import Count


def entry_list(request):
    entries = Balance.objects.all().order_by('-date')
    for entry in entries:
        entry.profit = entry.payout - entry.investment
    return render(request, 'balance/entry_list.html', {'entries': entries, 'url': 'all'})


def my_list(request):
    # ログイン中のユーザーに関連するBalanceオブジェクトを日付の降順で取得
    entries = Balance.objects.filter(user=request.user).order_by('-date', '-id')
    for entry in entries:
        entry.profit = entry.payout - entry.investment
    return render(request, 'balance/entry_list.html', {'entries': entries, 'url': 'my'})


def create_entry(request):
    today = datetime.today().date()
    if request.method == 'POST':
        location_id = request.POST.get('location')
        hotel_id = request.POST.get('hotel')
        game_id = request.POST.get('game')
        investment = request.POST.get('investment')
        payout = request.POST.get('payout')
        comment = request.POST.get('comment')
        date = request.POST.get('date')

        # ログイン中のユーザーを取得
        user = request.user

        # LocationとHotelオブジェクトを取得
        location = Location.objects.get(id=location_id)
        hotel = Hotel.objects.get(id=hotel_id)
        game = Game.objects.get(id=game_id)

        # Balanceオブジェクトを作成
        balance = Balance.objects.create(
            user=user,
            location=location,
            game=game,
            hotel=hotel,
            investment=investment,
            payout=payout,
            comment=comment,
            date=date
        )
        return redirect('my_list')
    else:
        locations = Location.objects.all().order_by('name')
        hotels = Hotel.objects.all().order_by('name')
        games = Game.objects.all().order_by('name')
        return render(request, 'balance/entry_form.html', {'locations': locations, 'hotels': hotels,
                                                           'games': games, 'today': today})


def update_entry(request, pk):
    entry = Balance.objects.get(pk=pk)

    if request.method == 'POST':
        location_id = request.POST.get('location')
        hotel_id = request.POST.get('hotel')
        game_id = request.POST.get('game')
        investment = request.POST.get('investment')
        payout = request.POST.get('payout')
        comment = request.POST.get('comment')
        date = request.POST.get('date')

        # LocationとHotelオブジェクトを取得
        location = Location.objects.get(id=location_id)
        hotel = Hotel.objects.get(id=hotel_id)
        game = Game.objects.get(id=game_id)

        # Balanceオブジェクトを更新
        entry.location = location
        entry.hotel = hotel
        entry.game = game
        entry.investment = investment
        entry.payout = payout
        entry.comment = comment
        entry.date = date
        entry.save()

        return redirect('my_list')
    else:
        locations = Location.objects.all().order_by('name')
        hotels = Hotel.objects.all().order_by('name')
        games = Game.objects.all().order_by('name')
        return render(request, 'balance/entry_form.html', {'instance': entry, 'locations': locations,
                                                           'hotels': hotels, 'games': games})


def delete_entry(request, pk):
    entry = get_object_or_404(Balance, pk=pk)
    entry.delete()
    return redirect('my_list')


def custom_login(request):
    # GETパラメータからユーザー名とパスワードを取得
    username = request.GET.get('username')
    password = request.GET.get('password')

    # ユーザーの認証
    user = authenticate(request, username=username, password=password)

    if user is not None:
        # ユーザーが認証された場合、ログイン
        login(request, user)
        return HttpResponseRedirect(reverse('my_list'))
    else:
        # ユーザーが認証されなかった場合、エラーメッセージを返すなどの処理
        return HttpResponse("Invalid login.")


def all_users_graph(request):
    # 全てのユーザーを取得
    users = User.objects.all()
    games = Game.objects.all()
    hotels = Hotel.objects.all()
    locations = Location.objects.all()
    datas = []

    for user in users:
        # ゲーム別カウント
        game_count = []
        for game in games:
            game_count.append(
                {
                    'game': game.name,
                    'count': Balance.objects.filter(user=user, game=game).count(),
                }
            )
        total_game_count = Balance.objects.filter(user=user).count()
        game_count.append(
            {
                'game': 'Total',
                'count': total_game_count,
            }
        )

        # ロケーション別カウント（同日は重複排除する）
        location_count = []

        for location in locations:
            location_count.append(
                {
                    'location': location.name,
                    'count': Balance.objects.filter(user=user, location=location).values('date').annotate(total=Count('date')).count()
                }
            )
        location_count.append(
            {
                'location': 'Total',
                'count': Balance.objects.filter(user=user).values('date').annotate(total=Count('date')).count()
            }
        )

        # ゲーム別利益
        game_profit = []

        for game in games:
            game_balance = Balance.objects.filter(user=user, game=game).aggregate(
                sum_investment=Sum('investment'),
                sum_payout=Sum('payout')
            )

            if game_balance['sum_investment'] is None:
                game_summary = 0
            else:
                game_summary = game_balance['sum_payout'] - game_balance['sum_investment']

            game_profit.append(
                {
                    'game': game.name,
                    'profit': game_summary,
                }
            )
        game_balance = Balance.objects.filter(user=user).aggregate(
            sum_investment=Sum('investment'),
            sum_payout=Sum('payout'),
        )
        if game_balance['sum_investment'] is None:
            game_summary = 0
        else:
            game_summary = game_balance['sum_payout'] - game_balance['sum_investment']
        game_profit.append(
            {
                'game': 'Total',
                'profit': game_summary,
            }
        )

        # ホテルとゲーム別で損益
        hotel_game_profit = []
        for hotel in hotels:
            hotel_profit_by_hotelgame = []
            for game in games:
                game_profit_by_hotelgame = Balance.objects.filter(hotel=hotel, game=game, user=user).aggregate(
                total_profit=Sum('payout') - Sum('investment')
                )['total_profit'] or 0
                hotel_profit_by_hotelgame.append({
                    'game': game.name,
                    'profit': game_profit_by_hotelgame
                })
            game_profit_by_hotelgame = Balance.objects.filter(hotel=hotel, user=user).aggregate(
                total_profit=Sum('payout') - Sum('investment')
            )['total_profit'] or 0
            hotel_profit_by_hotelgame.append({
                'game': 'Total',
                'profit': game_profit_by_hotelgame
            })
            hotel_game_profit.append({
                'hotel': hotel.name,
                'games': hotel_profit_by_hotelgame
            })


        # ユーザーデータをテンプレートに渡す
        datas.append({'user': user, 'game_count': game_count, 'location_count': location_count,
                      'game_profit': game_profit, 'hotel_game_profit': hotel_game_profit})
    return render(request, 'balance/all_users_graph.html', {'datas': datas})


def my_graph(request):
    entries = Balance.objects.filter(user=request.user).order_by('date')
    daily_profits = []
    dates = []
    cumulative_profit = 0
    daily_date = entries.first().date
    for entry in entries:
        if not daily_date == entry.date:
            daily_profits.append(cumulative_profit)
            dates.append(daily_date)
            daily_date = entry.date
        profit = entry.payout - entry.investment
        cumulative_profit += profit
    daily_profits.append(cumulative_profit)
    dates.append(daily_date)

    entries = Balance.objects.filter(user=request.user).annotate(
        month=django.db.models.functions.TruncMonth('date')
    ).values('month').annotate(
        total_profit=Sum('payout') - Sum('investment')
    ).order_by('month')

    monthly_profits = [entry['total_profit'] for entry in entries]
    months = [entry['month'].strftime('%b %Y') for entry in entries]

    return render(request, 'balance/graph.html', {'entries': entries,
                                                  'daily_profits': daily_profits, 'dates': dates,
                                                  'monthly_profits': monthly_profits, 'months': months})


def entry_detail(request, pk):
    # データベースから該当するエントリーを取得
    entry = get_object_or_404(Balance, pk=pk)

    # テンプレートに渡すコンテキストを準備
    context = {
        'instance': entry
    }

    # テンプレートをレンダリングしてレスポンスを返す
    return render(request, 'balance/entry_detail.html', context)


def get_hotels(request):
    location_id = request.GET.get('location_id')
    hotels = Hotel.objects.filter(location_id=location_id).order_by('name').values_list('id', 'name')
    data = dict(hotels)
    return JsonResponse(data)
