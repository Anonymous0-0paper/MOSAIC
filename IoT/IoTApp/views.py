from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import IoTSerializer


class IoTView(viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=IoTSerializer.Start.StartRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='config/start')
    def start(self, request):
        serializer = IoTSerializer.Start.StartRequest(data=request.data)
        if serializer.is_valid():
            try:
                algorithm: str = serializer.validated_data['algorithm']
                output_name: str = serializer.validated_data['outputName']
            except Exception as e:
                return Response({
                    "message": e.args[0]
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                "message": f"IoT started running ..."
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
