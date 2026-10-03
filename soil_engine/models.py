from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class SoilTest(models.Model):
    """
    Soil test data following Indian soil testing standards (ICAR).
    Nutrient values in kg/ha, pH on standard scale.
    """
    SOIL_TYPE_CHOICES = [
        ('alluvial', 'Alluvial'),
        ('black', 'Black (Regur)'),
        ('red', 'Red'),
        ('laterite', 'Laterite'),
        ('desert', 'Desert (Arid)'),
        ('mountain', 'Mountain'),
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('loamy', 'Loamy'),
        ('silty', 'Silty'),
        ('clay_loam', 'Clay Loam'),
        ('sandy_loam', 'Sandy Loam'),
    ]

    TEXTURE_CHOICES = [
        ('fine', 'Fine'),
        ('medium', 'Medium'),
        ('coarse', 'Coarse'),
    ]

    # Identification
    sample_id = models.CharField(max_length=50, unique=True)
    farm_name = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, help_text="Village/District/State")
    area_hectares = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.01)],
        help_text="Farm area in hectares"
    )
    test_date = models.DateField(auto_now_add=True)

    # Soil Classification
    soil_type = models.CharField(max_length=20, choices=SOIL_TYPE_CHOICES, default='loamy')
    texture = models.CharField(max_length=10, choices=TEXTURE_CHOICES, default='medium')

    # Primary Nutrients (kg/ha)
    nitrogen = models.FloatField(
        help_text="Available Nitrogen (kg/ha). Low: <280, Medium: 280-560, High: >560",
        validators=[MinValueValidator(0), MaxValueValidator(1500)]
    )
    phosphorus = models.FloatField(
        help_text="Available Phosphorus P2O5 (kg/ha). Low: <10, Medium: 10-24.6, High: >24.6",
        validators=[MinValueValidator(0), MaxValueValidator(200)]
    )
    potassium = models.FloatField(
        help_text="Available Potassium K2O (kg/ha). Low: <108, Medium: 108-280, High: >280",
        validators=[MinValueValidator(0), MaxValueValidator(1000)]
    )

    # Soil Health Indicators
    ph = models.FloatField(
        help_text="Soil pH (0-14). Acidic: <6.5, Neutral: 6.5-7.5, Alkaline: >7.5",
        validators=[MinValueValidator(0), MaxValueValidator(14)]
    )
    organic_carbon = models.FloatField(
        help_text="Organic Carbon (%). Low: <0.5, Medium: 0.5-0.75, High: >0.75",
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    electrical_conductivity = models.FloatField(
        help_text="EC (dS/m). Normal: <1.0, Saline: >1.0",
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        default=0.5
    )

    # Secondary Nutrients (ppm)
    sulphur = models.FloatField(
        default=0, help_text="Available Sulphur (ppm). Deficient: <10",
        validators=[MinValueValidator(0)]
    )

    # Micronutrients (ppm)
    zinc = models.FloatField(
        default=0, help_text="Zinc (ppm). Deficient: <0.6",
        validators=[MinValueValidator(0)]
    )
    iron = models.FloatField(
        default=0, help_text="Iron (ppm). Deficient: <4.5",
        validators=[MinValueValidator(0)]
    )
    manganese = models.FloatField(
        default=0, help_text="Manganese (ppm). Deficient: <2.0",
        validators=[MinValueValidator(0)]
    )
    copper = models.FloatField(
        default=0, help_text="Copper (ppm). Deficient: <0.2",
        validators=[MinValueValidator(0)]
    )
    boron = models.FloatField(
        default=0, help_text="Boron (ppm). Deficient: <0.5",
        validators=[MinValueValidator(0)]
    )

    # Data Source & Provenance
    DATA_SOURCE_CHOICES = [
        ('manual_lab_test', 'Manual Soil Test Report (Lab)'),
        ('regional_api', 'Regional / Free Geo API Fallback'),
        ('soilgrids', 'ISRIC SoilGrids 2.0 Global API'),
        ('icar_taluk_card', 'ICAR Regional Taluk Health Card Database'),
    ]
    data_source = models.CharField(
        max_length=40, choices=DATA_SOURCE_CHOICES, default='manual_lab_test',
        help_text="Origin of soil test parameters"
    )
    source_details = models.CharField(
        max_length=255, blank=True,
        help_text="Detailed source attribution or matched Taluk/Gram Panchayat"
    )

    # Optional Crop & Age/Stage Input
    selected_crop = models.CharField(
        max_length=100, blank=True,
        help_text="Target crop chosen by user (optional)"
    )
    crop_age_years = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.1), MaxValueValidator(100)],
        help_text="Age in years (for Plantation / Perennial crops)"
    )
    growth_stage = models.CharField(
        max_length=30, blank=True,
        help_text="Current growth stage (for Field / Seasonal crops)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sample_id} - {self.location} ({self.test_date})"

    def get_n_status(self):
        if self.nitrogen < 280:
            return 'low'
        elif self.nitrogen <= 560:
            return 'medium'
        return 'high'

    def get_p_status(self):
        if self.phosphorus < 10:
            return 'low'
        elif self.phosphorus <= 24.6:
            return 'medium'
        return 'high'

    def get_k_status(self):
        if self.potassium < 108:
            return 'low'
        elif self.potassium <= 280:
            return 'medium'
        return 'high'

    def get_ph_status(self):
        if self.ph < 6.5:
            return 'acidic'
        elif self.ph <= 7.5:
            return 'neutral'
        return 'alkaline'

    def get_oc_status(self):
        if self.organic_carbon < 0.5:
            return 'low'
        elif self.organic_carbon <= 0.75:
            return 'medium'
        return 'high'


class WeatherData(models.Model):
    """
    Weather data for the farm location.
    """
    SEASON_CHOICES = [
        ('kharif', 'Kharif (Jun-Oct)'),
        ('rabi', 'Rabi (Nov-Mar)'),
        ('zaid', 'Zaid (Mar-Jun)'),
    ]

    location = models.CharField(max_length=200)
    date = models.DateField()
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)

    # Temperature
    temp_max = models.FloatField(help_text="Max temperature (°C)")
    temp_min = models.FloatField(help_text="Min temperature (°C)")
    temp_avg = models.FloatField(help_text="Average temperature (°C)")

    # Precipitation (Past & Forecast)
    rainfall_mm = models.FloatField(
        default=0, help_text="Total Rainfall (mm)",
        validators=[MinValueValidator(0)]
    )
    past_rainfall_7d_mm = models.FloatField(
        default=0, help_text="Past 7 days precipitation sum (mm)",
        validators=[MinValueValidator(0)]
    )
    forecast_rainfall_7d_mm = models.FloatField(
        default=0, help_text="Upcoming 7 days forecast precipitation sum (mm)",
        validators=[MinValueValidator(0)]
    )
    forecast_summary = models.TextField(
        blank=True, help_text="Agro-meteorological forecast summary and advisories"
    )
    weather_source = models.CharField(
        max_length=150, default="Open-Meteo Free Weather API",
        help_text="Origin of meteorological data"
    )
    humidity_percent = models.FloatField(
        default=60, help_text="Relative Humidity (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Wind
    wind_speed_kmh = models.FloatField(
        default=10, help_text="Wind Speed (km/h)",
        validators=[MinValueValidator(0)]
    )

    # Solar
    sunshine_hours = models.FloatField(
        default=6, help_text="Sunshine hours per day",
        validators=[MinValueValidator(0), MaxValueValidator(24)]
    )

    # Forecast flag
    is_forecast = models.BooleanField(
        default=False, help_text="Whether this is forecast data vs actual"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.location} - {self.date} ({self.season})"


class FertilizationHistory(models.Model):
    """
    Historical record of fertilizer applications on a farm.
    """
    FERTILIZER_TYPE_CHOICES = [
        ('urea', 'Urea (46-0-0)'),
        ('dap', 'DAP (18-46-0)'),
        ('mop', 'MOP (0-0-60)'),
        ('ssp', 'SSP (0-16-0)'),
        ('npk_10_26_26', 'NPK 10:26:26'),
        ('npk_12_32_16', 'NPK 12:32:16'),
        ('npk_20_20_0', 'NPK 20:20:0'),
        ('npk_15_15_15', 'NPK 15:15:15'),
        ('ammonium_sulphate', 'Ammonium Sulphate (20.6-0-0)'),
        ('zinc_sulphate', 'Zinc Sulphate'),
        ('borax', 'Borax'),
        ('fym', 'Farm Yard Manure'),
        ('vermicompost', 'Vermicompost'),
        ('neem_cake', 'Neem Cake'),
        ('gypsum', 'Gypsum'),
    ]

    APPLICATION_METHOD_CHOICES = [
        ('broadcasting', 'Broadcasting'),
        ('band_placement', 'Band Placement'),
        ('fertigation', 'Fertigation'),
        ('foliar', 'Foliar Spray'),
        ('spot', 'Spot Application'),
    ]

    CROP_STAGE_CHOICES = [
        ('basal', 'Basal (Pre-sowing)'),
        ('sowing', 'At Sowing'),
        ('tillering', 'Tillering/Vegetative'),
        ('flowering', 'Flowering'),
        ('fruiting', 'Fruiting/Grain Filling'),
        ('top_dressing', 'Top Dressing'),
    ]

    soil_test = models.ForeignKey(
        SoilTest, on_delete=models.CASCADE,
        related_name='fertilization_records'
    )
    application_date = models.DateField()
    crop_grown = models.CharField(max_length=100)
    fertilizer_type = models.CharField(max_length=30, choices=FERTILIZER_TYPE_CHOICES)
    quantity_kg_per_ha = models.FloatField(
        help_text="Quantity applied (kg/ha)",
        validators=[MinValueValidator(0)]
    )
    application_method = models.CharField(
        max_length=20, choices=APPLICATION_METHOD_CHOICES, default='broadcasting'
    )
    crop_stage = models.CharField(
        max_length=20, choices=CROP_STAGE_CHOICES, default='basal'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-application_date']
        verbose_name_plural = "Fertilization Histories"

    def __str__(self):
        return f"{self.crop_grown} - {self.get_fertilizer_type_display()} ({self.application_date})"


class CropSuggestion(models.Model):
    """
    Crop suggestions generated by the Soil Engine.
    """
    soil_test = models.ForeignKey(
        SoilTest, on_delete=models.CASCADE,
        related_name='crop_suggestions'
    )
    weather_data = models.ForeignKey(
        WeatherData, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    crop_name = models.CharField(max_length=100)
    suitability_score = models.FloatField(
        help_text="Suitability score (0-100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    reason = models.TextField(help_text="Why this crop is recommended")
    expected_yield_tonnes_per_ha = models.FloatField(
        default=0,
        help_text="Expected yield (tonnes/ha)"
    )
    season = models.CharField(max_length=10, default='kharif')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-suitability_score']

    def __str__(self):
        return f"{self.crop_name} (Score: {self.suitability_score})"


class FertilizationCycle(models.Model):
    """
    Next fertilization cycle recommendation from the Soil Engine.
    """
    soil_test = models.ForeignKey(
        SoilTest, on_delete=models.CASCADE,
        related_name='fertilization_cycles'
    )
    crop_name = models.CharField(max_length=100)
    crop_age_or_stage = models.CharField(max_length=100, blank=True, help_text="Crop age in years or growth stage")

    # Recommended fertilizers (JSON-like structured data)
    fertilizer_type = models.CharField(max_length=30)
    quantity_kg_per_ha = models.FloatField(validators=[MinValueValidator(0)])
    application_stage = models.CharField(max_length=50)
    recommended_date = models.DateField(null=True, blank=True)

    # Nutrient delivery
    nitrogen_delivered = models.FloatField(default=0, help_text="N delivered (kg/ha)")
    phosphorus_delivered = models.FloatField(default=0, help_text="P2O5 delivered (kg/ha)")
    potassium_delivered = models.FloatField(default=0, help_text="K2O delivered (kg/ha)")

    # Cost estimate
    estimated_cost_per_ha = models.FloatField(default=0, help_text="Estimated cost (₹/ha)")

    notes = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['recommended_date']

    def __str__(self):
        return f"{self.crop_name} - {self.fertilizer_type} ({self.quantity_kg_per_ha} kg/ha)"


class DerivativeForecast(models.Model):
    """
    Derivative forecasts computed from Soil Engine outputs.
    """
    FORECAST_TYPE_CHOICES = [
        ('crop_yield', 'Crop Yield'),
        ('fertilizer_demand', 'Fertilizer Demand Forecast'),
        ('equipment_demand', 'Farm Equipment Demand Forecast'),
        ('labor_demand', 'Labor Demand Forecast'),
        ('sub_derivative', 'Sub-derivative Demand Forecast'),
    ]

    soil_test = models.ForeignKey(
        SoilTest, on_delete=models.CASCADE,
        related_name='derivative_forecasts'
    )
    forecast_type = models.CharField(max_length=25, choices=FORECAST_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    value = models.FloatField(help_text="Forecast value")
    unit = models.CharField(max_length=50, help_text="Unit of measurement")
    confidence_percent = models.FloatField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence level of the forecast"
    )
    details = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['forecast_type']

    def __str__(self):
        return f"{self.get_forecast_type_display()}: {self.value} {self.unit}"
