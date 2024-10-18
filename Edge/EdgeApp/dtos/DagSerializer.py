from rest_framework import serializers

from .DAGSubTaskSerializer import DAGSubTaskSerializer


class DagSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    subtasks = serializers.ListField(child=DAGSubTaskSerializer())
    edges = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))
    deadline = serializers.IntegerField()
    arrivalTime = serializers.IntegerField()
