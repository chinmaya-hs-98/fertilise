from django import forms
from .models import SoilTest, WeatherData, FertilizationHistory
from .engine import CROP_DATABASE

CROP_CHOICES = [('', '-- Auto-Suggest Best Crops --')] + [
    (name, f"{name} ({data['category']})")
    for name, data in CROP_DATABASE.items()
]

GROWTH_STAGE_CHOICES = [
    ('basal', 'Basal (Sowing / Planting / Transplanting)'),
    ('vegetative', 'Vegetative (Tillering / Active Branching)'),
    ('flowering', 'Flowering (Panicle Initiation / Budding)'),
    ('fruiting', 'Fruiting (Grain / Pod Filling / Tuber Bulking)'),
    ('maturity', 'Maturity (Pre-Harvest)'),
]


class SoilTestForm(forms.ModelForm):
    """Form for inputting soil test data with pre-filled demo values and regional API autofill."""

    selected_crop = forms.ChoiceField(
        choices=CROP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_selected_crop'})
    )

    growth_stage = forms.ChoiceField(
        choices=GROWTH_STAGE_CHOICES,
        required=False,
        initial='basal',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_growth_stage'})
    )

    class Meta:
        model = SoilTest
        fields = [
            'sample_id', 'farm_name', 'location', 'area_hectares',
            'data_source', 'source_details',
            'selected_crop', 'crop_age_years', 'growth_stage',
            'soil_type', 'texture',
            'nitrogen', 'phosphorus', 'potassium',
            'ph', 'organic_carbon', 'electrical_conductivity',
            'sulphur', 'zinc', 'iron', 'manganese', 'copper', 'boron',
        ]
        widgets = {
            'sample_id': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., ST-2024-001',
            }),
            'farm_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., Green Fields Farm',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., Dharwad / Shimoga / Bellary / Nashik / Guntur',
                'id': 'id_location_input',
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0.01',
            }),
            'data_source': forms.Select(attrs={'class': 'form-select', 'id': 'id_data_source'}),
            'source_details': forms.HiddenInput(attrs={'id': 'id_source_details'}),
            'crop_age_years': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.5', 'min': '0.1', 'max': '100',
                'placeholder': 'e.g. 3.0 years',
                'id': 'id_crop_age_years',
            }),
            'soil_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_soil_type'}),
            'texture': forms.Select(attrs={'class': 'form-select', 'id': 'id_texture'}),
            'nitrogen': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'kg/ha (Low: <280)',
                'id': 'id_nitrogen',
            }),
            'phosphorus': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'kg/ha (Low: <10)',
                'id': 'id_phosphorus',
            }),
            'potassium': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'kg/ha (Low: <108)',
                'id': 'id_potassium',
            }),
            'ph': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0', 'max': '14',
                'placeholder': '0-14',
                'id': 'id_ph',
            }),
            'organic_carbon': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': '% (Low: <0.5)',
                'id': 'id_organic_carbon',
            }),
            'electrical_conductivity': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': 'dS/m (Normal: <1.0)',
                'id': 'id_electrical_conductivity',
            }),
            'sulphur': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'ppm',
                'id': 'id_sulphur',
            }),
            'zinc': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': 'ppm (Deficient: <0.6)',
                'id': 'id_zinc',
            }),
            'iron': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'ppm (Deficient: <4.5)',
                'id': 'id_iron',
            }),
            'manganese': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'ppm (Deficient: <2.0)',
                'id': 'id_manganese',
            }),
            'copper': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': 'ppm (Deficient: <0.2)',
                'id': 'id_copper',
            }),
            'boron': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.01', 'min': '0',
                'placeholder': 'ppm (Deficient: <0.5)',
                'id': 'id_boron',
            }),
        }


class WeatherDataForm(forms.ModelForm):
    """Form for weather data input with Open-Meteo live API autofill."""

    class Meta:
        model = WeatherData
        fields = [
            'location', 'date', 'season',
            'temp_max', 'temp_min', 'temp_avg',
            'rainfall_mm', 'past_rainfall_7d_mm', 'forecast_rainfall_7d_mm',
            'humidity_percent', 'wind_speed_kmh', 'sunshine_hours',
            'forecast_summary', 'weather_source', 'is_forecast',
        ]
        widgets = {
            'location': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., Bellary, Karnataka',
                'id': 'id_weather_location',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date', 'id': 'id_weather_date',
            }),
            'season': forms.Select(attrs={'class': 'form-select', 'id': 'id_weather_season'}),
            'temp_max': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'placeholder': '°C',
                'id': 'id_temp_max',
            }),
            'temp_min': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'placeholder': '°C',
                'id': 'id_temp_min',
            }),
            'temp_avg': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'placeholder': '°C',
                'id': 'id_temp_avg',
            }),
            'rainfall_mm': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0', 'placeholder': 'Total mm',
                'id': 'id_rainfall_mm',
            }),
            'past_rainfall_7d_mm': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0', 'placeholder': 'Past 7 days mm',
                'id': 'id_past_rainfall_7d_mm',
            }),
            'forecast_rainfall_7d_mm': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0', 'placeholder': 'Next 7 days mm',
                'id': 'id_forecast_rainfall_7d_mm',
            }),
            'humidity_percent': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '1', 'min': '0', 'max': '100',
                'placeholder': '%', 'id': 'id_humidity_percent',
            }),
            'wind_speed_kmh': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0', 'placeholder': 'km/h',
                'id': 'id_wind_speed_kmh',
            }),
            'sunshine_hours': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0', 'max': '24',
                'placeholder': 'hours', 'id': 'id_sunshine_hours',
            }),
            'forecast_summary': forms.Textarea(attrs={
                'class': 'form-textarea', 'rows': 2,
                'placeholder': 'Agro-meteorological forecast advisory...',
                'id': 'id_forecast_summary',
            }),
            'weather_source': forms.TextInput(attrs={
                'class': 'form-input', 'id': 'id_weather_source',
            }),
            'is_forecast': forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id_is_forecast'}),
        }


class FertilizationHistoryForm(forms.ModelForm):
    """Form for recording past fertilizer applications."""

    class Meta:
        model = FertilizationHistory
        fields = [
            'application_date', 'crop_grown', 'fertilizer_type',
            'quantity_kg_per_ha', 'application_method', 'crop_stage', 'notes',
        ]
        widgets = {
            'application_date': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date',
            }),
            'crop_grown': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., Rice (Paddy)',
            }),
            'fertilizer_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity_kg_per_ha': forms.NumberInput(attrs={
                'class': 'form-input', 'step': '0.1', 'min': '0',
                'placeholder': 'kg/ha',
            }),
            'application_method': forms.Select(attrs={'class': 'form-select'}),
            'crop_stage': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea', 'rows': 2,
                'placeholder': 'Any additional notes...',
            }),
        }
