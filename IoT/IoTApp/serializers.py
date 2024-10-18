from rest_framework import serializers

from .dtos.SubTaskSerializer import SubTaskSerializer


class IoTSerializer:
    class Start:
        class StartRequest(serializers.Serializer):
            algorithm = serializers.ChoiceField(choices=["MEES", "Locally", "Random", "HEFT_EDF", "Fuzzy"])
            outputName = serializers.CharField()

    class PushTask:
        class PushTaskRequest(serializers.Serializer):
            edgeAddress = serializers.CharField()
            task = SubTaskSerializer()
