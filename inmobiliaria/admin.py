from django.contrib import admin
from django import forms

from .models import (
    Categoria, Favorito, Imagen, Inmueble, Publicacion, Reseña,
    Rol, Solicitud, TipoInmueble, Ubicacion, Usuario,
)


class UsuarioForm(forms.ModelForm):
    nueva_contrasena = forms.CharField(
        label='Nueva contraseña', required=False, widget=forms.PasswordInput,
        help_text='Al editar, deja este campo vacío para conservar la contraseña.',
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'rol', 'correo', 'telefono', 'estado']

    def clean_nueva_contrasena(self):
        contrasena = self.cleaned_data['nueva_contrasena']
        if not self.instance.pk and not contrasena:
            raise forms.ValidationError('Escribe una contraseña para el usuario.')
        return contrasena

    def save(self, commit=True):
        usuario = super().save(commit=False)
        contrasena = self.cleaned_data['nueva_contrasena']
        if contrasena:
            usuario.guardar_contraseña(contrasena)
        if commit:
            usuario.save()
        return usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    form = UsuarioForm
    list_display = ['nombre', 'correo', 'estado']


admin.site.register([
    Rol, Categoria, TipoInmueble, Ubicacion, Inmueble,
    Imagen, Publicacion, Solicitud, Reseña, Favorito,
])
