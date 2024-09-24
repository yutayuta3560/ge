import datetime
import django.db.models.functions
from django.shortcuts import get_object_or_404
from .models import Balance, Location, Hotel, Game
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Value, DecimalField, FloatField
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime, timedelta
from .forms import SignUpForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied


def entry_list(request):
    if not request.user.first_name == '1':
        return my_list(request)

    entries = Balance.objects.all().order_by('-date', '-id')
    paginator = Paginator(entries, 10)
    page_number = request.GET.get('page')
    entries = paginator.get_page(page_number)
    return render(request, 'balance/entry_list.html', {'entries': entries, 'url': 'all'})


def my_list(request):
    # ログイン中のユーザーに関連するBalanceオブジェクトを日付の降順で取得
    entries = Balance.objects.filter(user=request.user).order_by('-date', '-id')
    paginator = Paginator(entries, 10)
    page_number = request.GET.get('page')
    entries = paginator.get_page(page_number)
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

    if entry.user != request.user:
        # ユーザーが異なる場合は403エラーを返す
        raise PermissionDenied

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

    if entry.user != request.user:
        # ユーザーが異なる場合は403エラーを返す
        raise PermissionDenied

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
    games = Game.objects.all().order_by('name')
    hotels = Hotel.objects.all()
    locations = Location.objects.all()
    datas = []

    for user in users:
        if not request.user.first_name == '1' and not user.username == request.user.username:
            continue

        # ゲーム別カウントと利益の一覧
        game_balances = Balance.objects.filter(user=user).values('game__name').annotate(
            total_profit=Coalesce(Sum('profit', output_field=DecimalField()),
                                  Value(Decimal('0.00'), output_field=DecimalField())),
            sum_investment=Coalesce(Sum('investment', output_field=DecimalField()),
                                    Value(Decimal('0.00'), output_field=DecimalField())),
            sum_payout=Coalesce(Sum('payout', output_field=DecimalField()),
                                Value(Decimal('0.00'), output_field=DecimalField())),
            count=Count('id')
        )

        game_totals = {'sum_investment': Decimal('0.00'), 'sum_payout': Decimal('0.00'),
                       'total_profit': Decimal('0.00'), 'count': 0}

        # ゲーム別データを初期化
        game_name_to_data = {game.name: {'sum_investment': Decimal('0.00'), 'sum_payout': Decimal('0.00'),
                                         'total_profit': Decimal('0.00'), 'count': 0} for game in games}

        # データを集計
        for balance in game_balances:
            game_name = balance['game__name']
            sum_investment = balance['sum_investment']
            sum_payout = balance['sum_payout']
            total_profit = balance['total_profit']
            count = balance['count']

            game_name_to_data[game_name] = {
                'sum_investment': sum_investment,
                'sum_payout': sum_payout,
                'total_profit': total_profit,
                'count': count
            }

            # 合計を計算
            game_totals['sum_investment'] += sum_investment
            game_totals['sum_payout'] += sum_payout
            game_totals['total_profit'] += total_profit
            game_totals['count'] += count

        # summary_per_gameを固定された順序で構築
        summary_per_game = []
        for game in games:
            data = game_name_to_data[game.name]
            sum_investment = data['sum_investment']
            sum_payout = data['sum_payout']
            total_profit = data['total_profit']
            count = data['count']

            if sum_investment == 0:
                location_yield = 100
            else:
                location_yield = round(sum_payout / sum_investment * 100, 2)

            summary_per_game.append({
                'game': game.name,
                'count': count,
                'profit': total_profit,
                'yield': location_yield,
            })

        # トータルの計算
        if game_totals['sum_investment'] == 0:
            total_yield = 100
        else:
            total_yield = round(game_totals['sum_payout'] / game_totals['sum_investment'] * 100, 2)

        summary_per_game.append({
            'game': 'Total',
            'count': game_totals['count'],
            'profit': game_totals['total_profit'],
            'yield': total_yield,
        })

        # ロケーション別カウント（同日は重複排除する）
        location_balances = Balance.objects.filter(user=user).values('location__name').annotate(
            total_profit=Coalesce(Sum('profit', output_field=DecimalField()),
                                  Value(Decimal('0.00'), output_field=DecimalField())),
            count=Count('date', distinct=True)
        )

        # ロケーション別データを初期化
        location_name_to_data = {location.name: {'profit': Decimal('0.00'), 'count': 0} for location in locations}

        # データを集計
        for balance in location_balances:
            location_name = balance['location__name']
            total_profit = balance['total_profit']
            count = balance['count']

            location_name_to_data[location_name] = {
                'profit': total_profit,
                'count': count
            }

        # location_countを固定された順序で構築
        location_count = []
        total_location_profit = Decimal('0.00')
        total_location_count = 0

        for location in locations:
            data = location_name_to_data[location.name]
            profit = data['profit']
            count = data['count']

            location_count.append({
                'location': location.name,
                'count': count,
                'profit': profit,
            })

            # トータルの計算
            total_location_profit += profit
            total_location_count += count

        location_count.append({
            'location': 'Total',
            'count': total_location_count,
            'profit': total_location_profit,
        })

        # ホテルとゲーム別で損益
        hotel_game_profit = []

        for hotel in hotels:
            balances = Balance.objects.filter(user=user, hotel=hotel).values('game__name').annotate(
                total_profit=Coalesce(Sum('profit', output_field=DecimalField()),
                                      Value(Decimal('0.00'), output_field=DecimalField())),
                count=Count('id')
            )

            # ゲーム別データを初期化
            game_data = {game.name: {'profit': Decimal('0.00'), 'count': 0} for game in games}

            # データを集計
            for balance in balances:
                game_name = balance['game__name']
                total_profit = balance['total_profit']
                count = balance['count']

                game_data[game_name] = {
                    'profit': total_profit,
                    'count': count
                }

            hotel_profit_by_hotelgame = []
            total_profit_hotel = Decimal('0.00')
            total_count_hotel = 0

            for game in games:
                data = game_data[game.name]
                profit = data['profit']
                count = data['count']

                hotel_profit_by_hotelgame.append({
                    'game': game.name,
                    'count': count,
                    'profit': profit
                })

                total_profit_hotel += profit
                total_count_hotel += count

            if total_count_hotel > 0:
                hotel_profit_by_hotelgame.append({
                    'game': 'Total',
                    'count': total_count_hotel,
                    'profit': total_profit_hotel,
                })

                hotel_game_profit.append({
                    'hotel': hotel.short_name,
                    'games': hotel_profit_by_hotelgame
                })

        # 日付別で損益
        daily_balances = Balance.objects.filter(
            user=user,
            date__gte=datetime.today().date() - timedelta(days=4)
        ).values('date').annotate(
            total_profit=Coalesce(Sum('profit', output_field=DecimalField()),
                                  Value(Decimal('0.00'), output_field=DecimalField()))
        )

        daily_profit_dict = {balance['date']: balance['total_profit'] for balance in daily_balances}

        daily_profit = []

        for delta in range(0, 5):
            day = datetime.today().date() - timedelta(days=delta)
            profit = daily_profit_dict.get(day, Decimal('0.00'))
            daily_profit.append({
                'date': day,
                'profit': profit,
            })

        datas.append({
            'user': user,
            'game_count': summary_per_game,
            'location_count': location_count,
            'hotel_game_profit': hotel_game_profit,
            'daily_profit': daily_profit,
        })

    return render(request, 'balance/all_users_graph.html', {'datas': datas})



def get_daily_profit(user, date):
    profit = (Balance.objects.filter(user=user, date=date)
    .annotate(daily_profit=Sum(F('payout') - F('investment'), output_field=FloatField()))
    .aggregate(total_profit=Sum('daily_profit'))['total_profit'])
    return profit if profit else 0  # 利益がない場合は0を返す


def my_graph(request):
    entries = Balance.objects.filter(user=request.user).order_by('date')

    if not entries:
        context = {}
        return render(request, 'balance/graph.html', context)

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

    if entry.user != request.user and not request.user.first_name == '1':
        # ユーザーが異なる場合は403エラーを返す
        raise PermissionDenied

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


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('my_list')  # 登録後にリダイレクトするページ
    else:
        form = SignUpForm()
    return render(request, 'balance/signup.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('my_list')  # ログイン後のリダイレクト先
    else:
        form = AuthenticationForm()
    return render(request, 'balance/login.html', {'form': form})
