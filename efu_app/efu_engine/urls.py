from django.urls import path, include
from rest_framework.routers import DefaultRouter
from efu_engine import views



# define router
router = DefaultRouter()
# register RecipeViewSet with 'recpies' with
router.register('rules', views.RuleViewSet)
router.register('rulesets', views.RuleSetViewSet)

app_name = 'efu_engine'

# register default for the 'recipe' router
urlpatterns = [
    path('', include(router.urls)),
]
