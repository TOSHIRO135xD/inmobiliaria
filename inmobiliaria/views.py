from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Categoria, Inmueble
from .serializers import CategoriaSerializer, InmuebleSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.prefetch_related('inmuebles').order_by('id')
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'error': 'No se puede eliminar una categoría que tiene inmuebles.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InmuebleViewSet(viewsets.ModelViewSet):
    queryset = Inmueble.objects.select_related('categoria').order_by('id')
    serializer_class = InmuebleSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        titulo = serializer.validated_data['titulo'].strip()
        serializer.save(titulo=titulo)

    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        inmueble = self.get_object()
        if inmueble.estado != Inmueble.EstadoInmueble.DISPONIBLE:
            return Response(
                {'error': 'Solo se puede pausar un inmueble disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        inmueble.pausar()
        return Response(self.get_serializer(inmueble).data)

    @action(detail=True, methods=['post'], url_path='marcar-arrendado')
    def marcar_arrendado(self, request, pk=None):
        inmueble = self.get_object()
        if inmueble.operacion != Inmueble.Operacion.ARRIENDO:
            return Response(
                {'error': 'El inmueble debe estar en arriendo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if inmueble.estado != Inmueble.EstadoInmueble.DISPONIBLE:
            return Response(
                {'error': 'Solo se puede arrendar un inmueble disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        inmueble.marcar_como_arrendado()
        return Response(self.get_serializer(inmueble).data)
