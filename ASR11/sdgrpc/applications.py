import math
import os
import socket

import grpc
from sdgrpc import contracts_pb2 as pb
from sdgrpc import contracts_pb2_grpc as rpc


class CalculatorService(rpc.CalculatorServiceServicer):
    def Calculate(self, request, context):
        if not (math.isfinite(request.a) and math.isfinite(request.b)):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Os operandos devem ser numeros finitos.")
        if request.operation == pb.ADD:
            result = request.a + request.b
        elif request.operation == pb.SUBTRACT:
            result = request.a - request.b
        elif request.operation == pb.MULTIPLY:
            result = request.a * request.b
        elif request.operation == pb.DIVIDE:
            if request.b == 0:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Divisao por zero.")
            result = request.a / request.b
        else:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Operacao desconhecida.")
        if not math.isfinite(result):
            context.abort(grpc.StatusCode.OUT_OF_RANGE, "Resultado fora do intervalo representavel.")
        return pb.CalculationResult(result=result, machine=socket.gethostname(), process_id=os.getpid())


class TextService(rpc.TextServiceServicer):
    def Analyze(self, request, context):
        if len(request.text) > 10000:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "O texto pode ter ate 10000 caracteres.")
        return pb.TextAnalysis(
            uppercase=request.text.upper(), characters=len(request.text), words=len(request.text.split()),
            machine=socket.gethostname(), process_id=os.getpid(),
        )
