from rest_framework import serializers


class DAGSubTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=['SOFT', 'FIRM', 'HARD'])
    executionCost = serializers.IntegerField()
    memory = serializers.IntegerField()
