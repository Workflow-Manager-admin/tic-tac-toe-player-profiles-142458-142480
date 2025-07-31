from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('games/start/', views.start_game, name='start-game'),
    path('games/<str:game_id>/move/', views.make_move, name='make-move'),
    path('games/<str:game_id>/', views.game_state, name='game-state'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('users/<str:user_id>/games/', views.user_games, name='user-games'),
    path('health/', views.health, name='Health'),
]
