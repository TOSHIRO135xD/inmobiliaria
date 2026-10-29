from rest_framework import serializers

from .models import Categoria, Inmueble


class InmuebleResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inmueble
        fields = ['id', 'titulo', 'precio', 'operacion', 'estado']


class CategoriaSerializer(serializers.ModelSerializer):
    inmuebles = InmuebleResumenSerializer(many=True, read_only=True)

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'inmuebles']


class InmuebleSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')

    class Meta:
        model = Inmueble
        fields = [
            'id', 'usuario', 'categoria', 'categoria_nombre', 'ubicacion',
            'tipo_inmueble', 'titulo', 'descripcion', 'precio', 'operacion',
            'estado', 'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']

    def validate_precio(self, value):
        if value <= 0:
            raise serializers.ValidationError('El precio debe ser mayor que cero.')
        return value

    def validate(self, attrs):
        operacion = attrs.get('operacion', getattr(self.instance, 'operacion', None))
        estado = attrs.get('estado', getattr(self.instance, 'estado', None))
        if estado == Inmueble.EstadoInmueble.ARRENDADO and operacion != Inmueble.Operacion.ARRIENDO:
            raise serializers.ValidationError({'estado': 'Solo se puede arrendar un inmueble en arriendo.'})
        if estado == Inmueble.EstadoInmueble.VENDIDO and operacion != Inmueble.Operacion.VENTA:
            raise serializers.ValidationError({'estado': 'Solo se puede vender un inmueble en venta.'})
        return attrs

    def create(self, validated_data):
        return Inmueble.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.usuario = validated_data.get('usuario', instance.usuario)
        instance.categoria = validated_data.get('categoria', instance.categoria)
        instance.ubicacion = validated_data.get('ubicacion', instance.ubicacion)
        instance.tipo_inmueble = validated_data.get('tipo_inmueble', instance.tipo_inmueble)
        instance.titulo = validated_data.get('titulo', instance.titulo)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.precio = validated_data.get('precio', instance.precio)
        instance.operacion = validated_data.get('operacion', instance.operacion)
        instance.estado = validated_data.get('estado', instance.estado)
        instance.save()
        return instance
