from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .device import DEVICE
from .dtos.EdgeSerializer import EdgeSerializer
from .dtos.FogSerializer import FogSerializer
from .dtos.SubTaskSerializer import SubTaskSerializer
from .serializers import CloudSerializer


class CloudView(viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=CloudSerializer.Start.StartRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='config/start')
    def start(self, request):
        serializer = CloudSerializer.Start.StartRequest(data=request.data)
        if serializer.is_valid():
            try:
                algorithm: str = serializer.validated_data['algorithm']
                output_name: str = serializer.validated_data['outputName']
                DEVICE.start(algorithm, output_name)
            except Exception as e:
                return Response({
                    "message": e.args[0]
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                "message": f"Cloud started running ..."
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=FogSerializer,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='config/registerFog')
    def registerFog(self, request):
        serializer = FogSerializer(data=request.data)
        if serializer.is_valid():
            DEVICE.register_fog(serializer.validated_data)
            return Response({"message": f"Fog node registered."})
        else:
            return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        request_body=EdgeSerializer,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='config/registerEdge')
    def registerEdge(self, request):
        serializer = EdgeSerializer(data=request.data)
        if serializer.is_valid():
            DEVICE.register_edge(serializer.validated_data)
            return Response({"message": f"Edge device registered."})
        else:
            return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['get'], url_path='config/getNodes')
    def getNodes(self, request):
        fogs, edges = DEVICE.get_nodes()
        serializer = CloudSerializer.GetNodes.GetNodesResponse(fogs, edges)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)


    @swagger_auto_schema(
        request_body=CloudSerializer.PushTask.PushTaskRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='tasks/pushTask')
    def pushTask(self, request):
        serializer = CloudSerializer.PushTask.PushTaskRequest(data=request.data)
        if serializer.is_valid():
            edge_address: str = serializer.validated_data['edgeAddress']
            task: SubTaskSerializer = serializer.validated_data['task']
            DEVICE.add_task(edge_address, task)
            return Response({"message": f"task added."})
        else:
            return Response(serializer.errors, status=400)
