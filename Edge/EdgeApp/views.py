from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .device import DEVICE
from .dtos.DagSerializer import DagSerializer
from .dtos.PeriodicTaskSerializer import PeriodicTaskSerializer
from .serializers import EdgeSerializer


class EdgeView(viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=EdgeSerializer.Start.StartRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['post'], url_path='config/start')
    def start(self, request):
        serializer = EdgeSerializer.Start.StartRequest(data=request.data)
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
                "message": f"Edge started running ..."
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter('maxCount', openapi.IN_QUERY, type=openapi.TYPE_NUMBER)],
        responses={200: 'Success'}
    )
    @action(detail=False, methods=['get'], url_path='config/position')
    def get_last_positions(self, request):
        max_count: int = int(request.GET.get('maxCount'))
        positions = DEVICE.get_last_positions(max_count)
        serializer = EdgeSerializer.GetPositions.GetPositionsResponse(DEVICE.walk_model, positions)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        request_body=EdgeSerializer.PushDAGTasks.PushDAGTasksRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['patch'], url_path='tasks/pushDAGs')
    def pushDAGTasks(self, request):
        serializer = EdgeSerializer.PushDAGTasks.PushDAGTasksRequest(data=request.data)
        if serializer.is_valid():
            dags: list[DagSerializer] = serializer.validated_data['dags']
            DEVICE.add_dags(dags)
            return Response({"message": f" {len(dags)} DAGs added."})
        else:
            return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        request_body=EdgeSerializer.PushPeriodicTasks.PushPeriodicTasksRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['patch'], url_path='tasks/pushPeriodicTasks')
    def pushPeriodicTasks(self, request):
        serializer = EdgeSerializer.PushPeriodicTasks.PushPeriodicTasksRequest(data=request.data)
        if serializer.is_valid():
            tasks: list[PeriodicTaskSerializer] = serializer.validated_data['tasks']
            DEVICE.add_periodic_tasks(tasks)
            return Response({"message": f" {len(tasks)} tasks added."})
        else:
            return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        request_body=EdgeSerializer.NotifyExecuteTask.NotifyExecuteTaskRequest,
        responses={200: 'Success', 400: 'Bad request'}
    )
    @action(detail=False, methods=['patch'], url_path='tasks/notifyExecuteTask')
    def notifyExecuteTask(self, request):
        serializer = EdgeSerializer.NotifyExecuteTask.NotifyExecuteTaskRequest(data=request.data)
        if serializer.is_valid():
            task_id: int = serializer.validated_data['taskId']
            workflow_id: int = serializer.validated_data['workflowId']
            job_id: int = serializer.validated_data['jobId']
            DEVICE.notify_execute_task(task_id, workflow_id, job_id)
            return Response({"message": f"Received."})
        else:
            return Response(serializer.errors, status=400)
