from rest_framework import serializers

from .device import WalkMode
from .dtos.DagSerializer import DagSerializer
from .dtos.PeriodicTaskSerializer import PeriodicTaskSerializer


class EdgeSerializer:
    class Start:
        class StartRequest(serializers.Serializer):
            algorithm = serializers.ChoiceField(choices=["MEES", "Locally", "Random", "HEFT_EDF", "Fuzzy"])
            outputName = serializers.CharField()

    class GetPositions:
        class GetPositionsResponse(serializers.Serializer):
            def __init__(self, walk_model, positions):
                data = {
                    'walkModel': walk_model,
                    'positions': positions,
                }
                super().__init__(data=data)

            walkModel = serializers.ChoiceField(choices=[v.value for v in WalkMode])
            positions = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))

    class PushDAGTasks:
        class PushDAGTasksRequest(serializers.Serializer):
            dags = serializers.ListField(child=DagSerializer())

    class PushPeriodicTasks:
        class PushPeriodicTasksRequest(serializers.Serializer):
            tasks = serializers.ListField(child=PeriodicTaskSerializer())

    class NotifyExecuteTask:
        class NotifyExecuteTaskRequest(serializers.Serializer):
            taskId = serializers.IntegerField()
            workflowId = serializers.IntegerField()
            jobId = serializers.IntegerField()
