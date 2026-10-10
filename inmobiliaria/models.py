
from django.db import models
from django.contrib.auth.hashers import make_password



class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre



class Usuario(models.Model):

    class EstadoUsuario(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"
        BLOQUEADO = "bloqueado", "Bloqueado"

    nombre = models.CharField(max_length=100)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name="usuarios"
    )
    correo = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=128)
    telefono = models.CharField(max_length=20, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoUsuario.choices,
        default=EstadoUsuario.ACTIVO
    )

    def guardar_contraseña(self, contraseña):
        self.contraseña = make_password(contraseña)

    def __str__(self):
        return self.nombre



class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre



class TipoInmueble(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nombre


class Ubicacion(models.Model):
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    barrio = models.CharField(max_length=100, blank=True)
    latitud = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )
    longitud = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.direccion}, {self.ciudad}"



class Inmueble(models.Model):

    class Operacion(models.TextChoices):
        VENTA = "venta", "Venta"
        ARRIENDO = "arriendo", "Arriendo"

    class EstadoInmueble(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        ARRENDADO = "arrendado", "Arrendado"
        VENDIDO = "vendido", "Vendido"
        INACTIVO = "inactivo", "Inactivo"

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="inmuebles"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="inmuebles"
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name="inmuebles"
    )
    tipo_inmueble = models.ForeignKey(
        TipoInmueble,
        on_delete=models.PROTECT,
        related_name="inmuebles"
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )
    operacion = models.CharField(
        max_length=20,
        choices=Operacion.choices
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoInmueble.choices,
        default=EstadoInmueble.DISPONIBLE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def crear(self):
        self.save()

    def editar(self, **datos):
        for campo, valor in datos.items():
            if campo in {
                "titulo",
                "descripcion",
                "precio",
                "operacion",
                "estado",
                "categoria",
                "ubicacion",
                "tipo_inmueble",
            }:
                setattr(self, campo, valor)

        self.save()

    def pausar(self):
        self.estado = self.EstadoInmueble.INACTIVO
        self.save(update_fields=["estado"])

    def marcar_como_arrendado(self):
        self.estado = self.EstadoInmueble.ARRENDADO
        self.save(update_fields=["estado"])

    def __str__(self):
        return self.titulo



class Imagen(models.Model):
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )
    url = models.URLField(max_length=500)
    orden = models.PositiveIntegerField(default=1)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return f"Imagen {self.orden} - {self.inmueble.titulo}"



class Publicacion(models.Model):
    inmueble = models.OneToOneField(
        Inmueble,
        on_delete=models.CASCADE,
        related_name="publicacion"
    )
    visible = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Publicación: {self.inmueble.titulo}"



class Solicitud(models.Model):

    class TipoSolicitud(models.TextChoices):
        INFORMACION = "informacion", "Solicitar información"
        VISITA = "visita", "Solicitar visita"
        COMPRA = "compra", "Interés de compra"
        ARRIENDO = "arriendo", "Interés de arriendo"

    class EstadoSolicitud(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROCESO = "en_proceso", "En proceso"
        ATENDIDA = "atendida", "Atendida"
        CANCELADA = "cancelada", "Cancelada"

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="solicitudes"
    )
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name="solicitudes"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoSolicitud.choices
    )
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PENDIENTE
    )

    def __str__(self):
        return f"Solicitud #{self.id} - {self.inmueble.titulo}"



class Reseña(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="reseñas"
    )
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name="reseñas"
    )
    calificacion = models.PositiveSmallIntegerField()
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(calificacion__gte=1)
                & models.Q(calificacion__lte=5),
                name="calificacion_entre_1_y_5"
            )
        ]

    def __str__(self):
        return f"Reseña de {self.usuario.nombre} - {self.calificacion}/5"



class Favorito(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="favoritos"
    )
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.CASCADE,
        related_name="favoritos"
    )
    fecha_guardado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_guardado"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "inmueble"],
                name="favorito_unico_por_usuario"
            )
        ]

    def __str__(self):
        return f"{self.usuario.nombre} - {self.inmueble.titulo}"
