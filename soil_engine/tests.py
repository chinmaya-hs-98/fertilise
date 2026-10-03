from django.test import TestCase, Client
from django.urls import reverse
from datetime import date

from .models import SoilTest, WeatherData, FertilizationHistory, CropSuggestion, FertilizationCycle
from .engine import SoilEngine, CROP_DATABASE
from .geo_soil_service import fetch_geo_soil_data


class GeoSoilServiceTests(TestCase):
    def test_taluk_lookup_dharwad(self):
        data = fetch_geo_soil_data("Dharwad, Karnataka")
        self.assertIsNotNone(data)
        self.assertEqual(data['soil_type'], 'black')
        self.assertGreater(data['confidence'], 80)
        self.assertIn('Karnataka', data['location_matched'])

    def test_taluk_lookup_shimoga(self):
        data = fetch_geo_soil_data("Shivamogga, Karnataka")
        self.assertIsNotNone(data)
        self.assertEqual(data['soil_type'], 'laterite')
        self.assertLess(data['ph'], 6.5)

    def test_geo_fallback_unknown_location(self):
        data = fetch_geo_soil_data("Random Remote Valley 12345")
        self.assertIsNotNone(data)
        self.assertIn('nitrogen', data)
        self.assertIn('ph', data)
        self.assertTrue(data.get('is_regional_fallback'))


class SoilEnginePlantationAgeTests(TestCase):
    def setUp(self):
        self.soil = SoilTest.objects.create(
            sample_id="TEST-ARECA-001",
            farm_name="Areca Estate",
            location="Thirthahalli, Shimoga",
            area_hectares=1.0,
            soil_type="laterite",
            texture="medium",
            nitrogen=280.0,
            phosphorus=15.0,
            potassium=160.0,
            ph=5.8,
            organic_carbon=0.85,
            electrical_conductivity=0.25,
            selected_crop="Arecanut (Betel Nut)",
            crop_age_years=1.0,
        )
        self.weather = WeatherData.objects.create(
            location=self.soil.location,
            date=date.today(),
            season='kharif',
            temp_max=30.0,
            temp_min=22.0,
            temp_avg=26.0,
            rainfall_mm=160.0,
            humidity_percent=80.0,
            wind_speed_kmh=10.0,
            sunshine_hours=5.5,
        )

    def test_arecanut_year1_scaled_dose(self):
        # Year 1 seedling dose is ~33% of adult dose
        engine_y1 = SoilEngine(
            soil_test=self.soil,
            weather_data=self.weather,
            target_crop="Arecanut (Betel Nut)",
            crop_age_years=1.0,
        )
        plan_y1 = engine_y1.get_fertilization_plan()
        total_cost_y1 = sum(f['cost_per_ha'] for f in plan_y1)

        # Adult dose (Year 4+)
        engine_y4 = SoilEngine(
            soil_test=self.soil,
            weather_data=self.weather,
            target_crop="Arecanut (Betel Nut)",
            crop_age_years=4.0,
        )
        plan_y4 = engine_y4.get_fertilization_plan()
        total_cost_y4 = sum(f['cost_per_ha'] for f in plan_y4)

        # Year 1 dose should be significantly smaller than adult Year 4 dose
        self.assertLess(total_cost_y1, total_cost_y4)
        self.assertTrue(any(f.get('quantity_per_plant_g') is not None for f in plan_y1))

    def test_field_crop_growth_stage(self):
        engine_veg = SoilEngine(
            soil_test=self.soil,
            weather_data=self.weather,
            target_crop="Rice (Paddy)",
            growth_stage="vegetative",
        )
        plan_veg = engine_veg.get_fertilization_plan()
        self.assertTrue(len(plan_veg) > 0)


class ViewsAndApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_geo_soil_api_endpoint(self):
        response = self.client.get(reverse('soil_engine:api_geo_soil'), {'location': 'Dharwad'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['soil_type'], 'black')
        self.assertIn('nitrogen', data)

    def test_crop_database_api(self):
        response = self.client.get(reverse('soil_engine:api_crops'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('Arecanut (Betel Nut)', data['crops'])
        self.assertIn('Rice (Paddy)', data['crops'])

    def test_soil_input_page(self):
        response = self.client.get(reverse('soil_engine:soil_input'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Auto-Fetch by Geography')
        self.assertContains(response, 'Plantation Age (in Years)')
