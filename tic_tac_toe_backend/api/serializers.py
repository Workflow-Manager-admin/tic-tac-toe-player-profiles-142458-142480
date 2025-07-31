from rest_framework import serializers

# PUBLIC_INTERFACE
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=128)

# PUBLIC_INTERFACE
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=128)

# PUBLIC_INTERFACE
class StartGameSerializer(serializers.Serializer):
    opponent_username = serializers.CharField(max_length=32)

# PUBLIC_INTERFACE
class MakeMoveSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    col = serializers.IntegerField()
    symbol = serializers.ChoiceField(choices=['X', 'O'])

# PUBLIC_INTERFACE
class GameResponseSerializer(serializers.Serializer):
    game_id = serializers.CharField()
    player_x = serializers.CharField()
    player_o = serializers.CharField()
    board = serializers.ListField(child=serializers.ListField(child=serializers.CharField(allow_blank=True)), min_length=3, max_length=3)
    current_turn = serializers.CharField()
    status = serializers.CharField()
    winner = serializers.CharField(allow_blank=True, required=False)
    draw = serializers.BooleanField()

# PUBLIC_INTERFACE
class LeaderboardUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    win_count = serializers.IntegerField()
    loss_count = serializers.IntegerField()
    draw_count = serializers.IntegerField()

# PUBLIC_INTERFACE
class GameHistoryEntrySerializer(serializers.Serializer):
    game_id = serializers.CharField()
    opponent = serializers.CharField()
    result = serializers.CharField()
    created_at = serializers.DateTimeField()
