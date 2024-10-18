from rest_framework import serializers


class FogSerializer(serializers.Serializer):
    address = serializers.CharField()
    positionX = serializers.IntegerField()
    positionY = serializers.IntegerField()
    coverageArea = serializers.IntegerField()

