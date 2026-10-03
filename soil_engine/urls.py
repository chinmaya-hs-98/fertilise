from django.urls import path
from . import views

app_name = 'soil_engine'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Input flow
    path('soil-input/', views.soil_input, name='soil_input'),
    path('weather-input/<int:soil_id>/', views.weather_input, name='weather_input'),
    path('history-input/<int:soil_id>/<int:weather_id>/', views.history_input, name='history_input'),

    # Quick analyze (skip weather/history)
    path('analyze/<int:soil_id>/', views.analyze, name='analyze'),

    # Results
    path('results/<int:soil_id>/<int:weather_id>/', views.results, name='results'),

    # Soil test management
    path('tests/', views.soil_test_list, name='soil_test_list'),
    path('tests/<int:soil_id>/', views.soil_test_detail, name='soil_test_detail'),

    # API endpoints
    path('api/geo-soil/', views.api_geo_soil_lookup, name='api_geo_soil'),
    path('api/geo-weather/', views.api_geo_weather, name='api_geo_weather'),
    path('api/crops/', views.api_crop_database, name='api_crops'),
    path('api/fertilizers/', views.api_fertilizer_database, name='api_fertilizers'),
]
