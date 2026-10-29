from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework.test import APITestCase

from .admin import UsuarioForm
from .models import Categoria, Inmueble, Rol, TipoInmueble, Ubicacion, Usuario


class InmobiliariaAPITests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='administrador', password='ClaveDePrueba123', is_staff=True,
        )
        self.client.force_authenticate(self.admin)
        self.rol = Rol.objects.create(nombre='Propietario')
        usuario = Usuario(nombre='Ana', correo='ana@example.com', rol=self.rol)
        usuario.guardar_contraseña('ClaveDePrueba123')
        usuario.save()
        self.categoria = Categoria.objects.create(nombre='Residencial')
        tipo = TipoInmueble.objects.create(nombre='Casa')
        ubicacion = Ubicacion.objects.create(direccion='Calle 1', ciudad='Mi pueblo')
        self.datos = {
            'usuario': usuario.pk, 'categoria': self.categoria.pk,
            'tipo_inmueble': tipo.pk, 'ubicacion': ubicacion.pk,
            'titulo': '  Casa en el centro  ', 'descripcion': 'Casa de dos pisos',
            'precio': '850000.00', 'operacion': 'arriendo',
        }

    def crear_inmueble(self):
        respuesta = self.client.post('/api/inmuebles/', self.datos, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        return respuesta.data['id']

    def test_crud_inmueble_y_categoria_anidada(self):
        pk = self.crear_inmueble()
        url = f'/api/inmuebles/{pk}/'
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.data['titulo'], 'Casa en el centro')
        self.assertEqual(respuesta.data['categoria_nombre'], 'Residencial')
        self.assertNotIn('contraseña', respuesta.data)
        self.assertEqual(len(self.client.get('/api/inmuebles/').data), 1)
        categoria = self.client.get(f'/api/categorias/{self.categoria.pk}/')
        self.assertEqual(categoria.data['inmuebles'][0]['id'], pk)
        respuesta = self.client.patch(url, {'precio': '900000.00'}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['precio'], '900000.00')
        self.assertEqual(respuesta.data['descripcion'], self.datos['descripcion'])
        respuesta = self.client.put(url, {**self.datos, 'titulo': 'Casa actualizada'}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['titulo'], 'Casa actualizada')
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_crud_categoria_y_borrado_protegido(self):
        respuesta = self.client.post('/api/categorias/', {'nombre': 'Comercial'})
        self.assertEqual(respuesta.status_code, 201)
        url = f"/api/categorias/{respuesta.data['id']}/"
        self.assertEqual(self.client.patch(url, {'nombre': 'Rural'}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.crear_inmueble()
        self.assertEqual(self.client.delete(f'/api/categorias/{self.categoria.pk}/').status_code, 400)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_datos_invalidos(self):
        for cambios in [
            {'precio': '-1'}, {'precio': '0'}, {'precio': None},
            {'categoria': 99999}, {'titulo': '   '}, {'operacion': 'otra'},
            {'operacion': 'venta', 'estado': 'arrendado'},
        ]:
            with self.subTest(cambios=cambios):
                respuesta = self.client.post('/api/inmuebles/', {**self.datos, **cambios}, format='json')
                self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Inmueble.objects.count(), 0)
        pk = self.crear_inmueble()
        self.assertEqual(self.client.patch(f'/api/inmuebles/{pk}/', {'precio': '-2'}).status_code, 400)

    def test_acciones_y_fecha_actualizacion(self):
        pk = self.crear_inmueble()
        fecha = Inmueble.objects.get(pk=pk).fecha_actualizacion
        respuesta = self.client.post(f'/api/inmuebles/{pk}/marcar-arrendado/')
        self.assertEqual(respuesta.status_code, 200)
        inmueble = Inmueble.objects.get(pk=pk)
        self.assertEqual(inmueble.estado, 'arrendado')
        self.assertGreater(inmueble.fecha_actualizacion, fecha)
        self.assertEqual(self.client.post(f'/api/inmuebles/{pk}/marcar-arrendado/').status_code, 400)
        self.assertEqual(self.client.post(f'/api/inmuebles/{pk}/pausar/').status_code, 400)
        self.assertEqual(self.client.patch(f'/api/inmuebles/{pk}/', {'operacion': 'venta'}).status_code, 400)
        otro = self.crear_inmueble()
        respuesta = self.client.post(f'/api/inmuebles/{otro}/pausar/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['estado'], 'inactivo')
        self.assertEqual(self.client.post('/api/inmuebles/99999/pausar/').status_code, 404)

    def test_no_arrendar_inmueble_en_venta(self):
        self.datos['operacion'] = 'venta'
        pk = self.crear_inmueble()
        self.assertEqual(self.client.post(f'/api/inmuebles/{pk}/marcar-arrendado/').status_code, 400)
        self.assertEqual(Inmueble.objects.get(pk=pk).estado, 'disponible')

    def test_acceso_solo_administrador(self):
        pk = self.crear_inmueble()
        usuario = get_user_model().objects.create_user(username='visitante')
        for persona in [None, usuario]:
            self.client.force_authenticate(persona)
            self.assertEqual(self.client.get('/api/categorias/').status_code, 403)
            self.assertEqual(self.client.get('/api/inmuebles/').status_code, 403)
            self.assertEqual(self.client.post('/api/inmuebles/', self.datos).status_code, 403)
            self.assertEqual(self.client.post(f'/api/inmuebles/{pk}/pausar/').status_code, 403)
            self.assertEqual(self.client.delete(f'/api/inmuebles/{pk}/').status_code, 403)

    def test_admin_guarda_contrasena_con_hash(self):
        datos = {
            'nombre': 'Luis', 'correo': 'luis@example.com', 'rol': self.rol.pk,
            'estado': 'activo', 'nueva_contrasena': 'MiClave123',
        }
        formulario = UsuarioForm(data=datos)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        usuario = formulario.save()
        self.assertTrue(check_password('MiClave123', usuario.contraseña))
        datos['nueva_contrasena'] = ''
        formulario = UsuarioForm(data=datos, instance=usuario)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertTrue(check_password('MiClave123', formulario.save().contraseña))
