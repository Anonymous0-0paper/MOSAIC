from rest_framework import serializers


class SubTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    workflowId = serializers.IntegerField()
    jobId = serializers.IntegerField()
    type = serializers.ChoiceField(choices=['SOFT', 'FIRM', 'HARD'])
    executionCost = serializers.IntegerField()
    memory = serializers.IntegerField()
    absoluteDeadline = serializers.FloatField()
