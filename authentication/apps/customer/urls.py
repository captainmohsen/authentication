from rest_framework import routers

from authentication.apps.customer import views

router = routers.SimpleRouter()
router.register(r"", views.CustomerViewSet)

urlpatterns = router.urls
