from django.views.generic import TemplateView

class DashboardView(TemplateView):
    """
    Главная страница дашборда — вес, питание, графики.
    Рендерит только HTML-скелет; данные подгружаются на клиенте
    через fetch() к DRF API. Авторизация проверяется в JS
    (наличие JWT в localStorage), а не на уровне Django.
    """
    template_name = 'frontend/dashboard.html'

class LoginView(TemplateView):
    """
    Страница логина. Форма дергает /api/token/ через JS,
    полученный access/refresh токен сохраняется в localStorage.
    """
    template_name = 'frontend/login.html'

