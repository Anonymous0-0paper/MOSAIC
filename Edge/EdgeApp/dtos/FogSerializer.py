from rest_framework import serializers


class FogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    address = serializers.CharField()
    positionX = serializers.IntegerField()
    positionY = serializers.IntegerField()
    coverageArea = serializers.IntegerField()
