from rest_framework import serializers


class PeriodicTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=['SOFT', 'FIRM', 'HARD'])
    executionCost = serializers.IntegerField()
    memory = serializers.IntegerField()
    deadline = serializers.IntegerField()
