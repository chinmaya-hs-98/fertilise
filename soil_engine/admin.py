from django.contrib import admin
from .models import (
    SoilTest, WeatherData, FertilizationHistory,
    CropSuggestion, FertilizationCycle, DerivativeForecast,
)


@admin.register(SoilTest)
class SoilTestAdmin(admin.ModelAdmin):
    list_display = ['sample_id', 'location', 'soil_type', 'ph', 'nitrogen', 'phosphorus', 'potassium', 'test_date']
    list_filter = ['soil_type', 'texture']
    search_fields = ['sample_id', 'location', 'farm_name']


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['location', 'date', 'season', 'temp_avg', 'rainfall_mm', 'humidity_percent']
    list_filter = ['season', 'is_forecast']
    search_fields = ['location']


@admin.register(FertilizationHistory)
class FertilizationHistoryAdmin(admin.ModelAdmin):
    list_display = ['soil_test', 'crop_grown', 'fertilizer_type', 'quantity_kg_per_ha', 'application_date']
    list_filter = ['fertilizer_type', 'application_method', 'crop_stage']


@admin.register(CropSuggestion)
class CropSuggestionAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'suitability_score', 'expected_yield_tonnes_per_ha', 'soil_test']
    list_filter = ['season']


@admin.register(FertilizationCycle)
class FertilizationCycleAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'fertilizer_type', 'quantity_kg_per_ha', 'application_stage', 'recommended_date']


@admin.register(DerivativeForecast)
class DerivativeForecastAdmin(admin.ModelAdmin):
    list_display = ['forecast_type', 'title', 'value', 'unit', 'confidence_percent']
    list_filter = ['forecast_type']
