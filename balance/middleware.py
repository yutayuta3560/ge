from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ログインが不要なURLを定義 (loginとsignupページ)
        exempt_urls = [reverse('custom_login'), reverse('custom_login2'), reverse('custom_login3'),
                       reverse('signup'), reverse('signup2')]

        # ユーザーがログインしていない場合
        if not request.user.is_authenticated:
            # 現在のURLが除外リストにない場合
            if request.path not in exempt_urls:
                return redirect('custom_login')  # ログインページにリダイレクト

        # リクエストを通常通り処理
        response = self.get_response(request)
        return response
