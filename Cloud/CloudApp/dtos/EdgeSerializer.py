from rest_framework import serializers


class EdgeSerializer(serializers.Serializer):
    address = serializers.CharField()

