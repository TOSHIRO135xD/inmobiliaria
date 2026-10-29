from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, InmuebleViewSet

router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='categoria')
router.register('inmuebles', InmuebleViewSet, basename='inmueble')

urlpatterns = router.urls
