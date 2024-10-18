from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .device import DEVICE
from .dtos.SubTaskSerializer import SubTaskSerializer
from .serializers import FogSerializer


class FogView(viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=FogSerializer.Start.StartRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='config/start')
    def start(self, request):
        serializer = FogSerializer.Start.StartRequest(data=request.data)
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
                "message": f"Fog started running ..."
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=FogSerializer.PushTask.PushTaskRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='tasks/pushTask')
    def pushTask(self, request):
        serializer = FogSerializer.PushTask.PushTaskRequest(data=request.data)
        if serializer.is_valid():
            edge_address: str = serializer.validated_data['edgeAddress']
            task: SubTaskSerializer = serializer.validated_data['task']
            DEVICE.add_task(edge_address, task)
            return Response({"message": f"task added."})
        else:
            return Response(serializer.errors, status=400)
