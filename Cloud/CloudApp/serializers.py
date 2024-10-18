from rest_framework import serializers

from .dtos.EdgeSerializer import EdgeSerializer
from .dtos.FogSerializer import FogSerializer
from .dtos.SubTaskSerializer import SubTaskSerializer
from .types.Edge import Edge
from .types.Fog import Fog


class CloudSerializer:
    class Start:
        class StartRequest(serializers.Serializer):
            algorithm = serializers.ChoiceField(choices=["MEES", "Locally", "Random", "HEFT_EDF", "Fuzzy"])
            outputName = serializers.CharField()

    class GetNodes:
        class GetNodesResponse(serializers.Serializer):
            def __init__(self, fogs: list[Fog], edges: list[Edge]):
                data = {
                    'edges': [
                        {
                            'address': edge.address
                        }
                        for edge in edges
                    ],
                    'fogs': [
                        {
                            'address': fog.address,
                            'positionX': fog.position_x,
                            'positionY': fog.position_y,
                            'coverageArea': fog.coverage_area
                        }
                        for fog in fogs
                    ],
                }
                super().__init__(data=data)

            fogs = serializers.ListField(child=FogSerializer())
            edges = serializers.ListField(child=EdgeSerializer())

    class PushTask:
        class PushTaskRequest(serializers.Serializer):
            edgeAddress = serializers.CharField()
            task = SubTaskSerializer()
