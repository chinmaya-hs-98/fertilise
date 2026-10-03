import json
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import (
    SoilTest, WeatherData, FertilizationHistory,
    CropSuggestion, FertilizationCycle, DerivativeForecast,
)
from .forms import SoilTestForm, WeatherDataForm, FertilizationHistoryForm
from .engine import SoilEngine, CROP_DATABASE, FERTILIZER_DATABASE
from .geo_soil_service import fetch_geo_soil_data
from .weather_service import fetch_live_weather


def dashboard(request):
    """Main dashboard view — landing page."""
    recent_tests = SoilTest.objects.all()[:6]
    total_tests = SoilTest.objects.count()
    total_suggestions = CropSuggestion.objects.count()
    total_cycles = FertilizationCycle.objects.count()

    context = {
        'recent_tests': recent_tests,
        'total_tests': total_tests,
        'total_suggestions': total_suggestions,
        'total_cycles': total_cycles,
    }
    return render(request, 'soil_engine/dashboard.html', context)


def soil_input(request):
    """Soil test data input view with pre-filled demo data & regional API autofill."""
    if request.method == 'POST':
        form = SoilTestForm(request.POST)
        if form.is_valid():
            soil_test = form.save()
            return redirect('soil_engine:analyze', soil_id=soil_test.id)
    else:
        # Pre-fill with demo data
        demo_data = {
            'sample_id': f'ST-{date.today().strftime("%Y%m%d")}-001',
            'farm_name': 'Demo Farm — Dharwad',
            'location': 'Dharwad, Karnataka',
            'area_hectares': 2.5,
            'data_source': 'manual_lab_test',
            'source_details': 'Lab Soil Test Report',
            'selected_crop': 'Arecanut (Betel Nut)',
            'crop_age_years': 3.0,
            'growth_stage': 'vegetative',
            'soil_type': 'black',
            'texture': 'medium',
            'nitrogen': 240.0,
            'phosphorus': 18.5,
            'potassium': 195.0,
            'ph': 7.2,
            'organic_carbon': 0.58,
            'electrical_conductivity': 0.42,
            'sulphur': 12.5,
            'zinc': 0.45,
            'iron': 5.8,
            'manganese': 3.2,
            'copper': 0.35,
            'boron': 0.42,
        }
        form = SoilTestForm(initial=demo_data)

    context = {
        'form': form,
        'page_title': 'Soil Test Data Input & Geo-API Fallback',
    }
    return render(request, 'soil_engine/soil_input.html', context)


def weather_input(request, soil_id):
    """Weather data input for a specific soil test with Open-Meteo live API integration."""
    soil_test = get_object_or_404(SoilTest, id=soil_id)

    if request.method == 'POST':
        form = WeatherDataForm(request.POST)
        if form.is_valid():
            weather = form.save()
            return redirect('soil_engine:history_input', soil_id=soil_id, weather_id=weather.id)
    else:
        # Pre-fill using live Open-Meteo API
        live_w = fetch_live_weather(soil_test.location)
        demo_data = {
            'location': soil_test.location,
            'date': date.today(),
            'season': live_w['season'],
            'temp_max': live_w['temp_max'],
            'temp_min': live_w['temp_min'],
            'temp_avg': live_w['temp_avg'],
            'rainfall_mm': live_w['rainfall_mm'],
            'past_rainfall_7d_mm': live_w['past_rainfall_7d_mm'],
            'forecast_rainfall_7d_mm': live_w['forecast_rainfall_7d_mm'],
            'humidity_percent': live_w['humidity_percent'],
            'wind_speed_kmh': live_w['wind_speed_kmh'],
            'sunshine_hours': live_w['sunshine_hours'],
            'forecast_summary': live_w['forecast_summary'],
            'weather_source': live_w['weather_source'],
            'is_forecast': True,
        }
        form = WeatherDataForm(initial=demo_data)

    context = {
        'form': form,
        'soil_test': soil_test,
        'page_title': 'Weather Data & Live Rainfall Forecast',
    }
    return render(request, 'soil_engine/weather_input.html', context)


def history_input(request, soil_id, weather_id):
    """Fertilization history input."""
    soil_test = get_object_or_404(SoilTest, id=soil_id)
    weather = get_object_or_404(WeatherData, id=weather_id)
    existing_history = FertilizationHistory.objects.filter(soil_test=soil_test)

    if request.method == 'POST':
        if 'skip' in request.POST:
            return redirect('soil_engine:results', soil_id=soil_id, weather_id=weather_id)

        form = FertilizationHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.soil_test = soil_test
            history.save()

            if 'add_another' in request.POST:
                return redirect('soil_engine:history_input', soil_id=soil_id, weather_id=weather_id)
            return redirect('soil_engine:results', soil_id=soil_id, weather_id=weather_id)
    else:
        demo_data = {
            'application_date': date.today() - timedelta(days=180),
            'crop_grown': 'Wheat',
            'fertilizer_type': 'dap',
            'quantity_kg_per_ha': 100.0,
            'application_method': 'broadcasting',
            'crop_stage': 'basal',
        }
        form = FertilizationHistoryForm(initial=demo_data)

    context = {
        'form': form,
        'soil_test': soil_test,
        'weather': weather,
        'existing_history': existing_history,
        'page_title': 'Fertilization History',
    }
    return render(request, 'soil_engine/history_input.html', context)


def analyze(request, soil_id):
    """
    Quick analyze view — skips manual weather/history input.
    Queries live Open-Meteo weather for that location and proceeds to results.
    """
    soil_test = get_object_or_404(SoilTest, id=soil_id)

    # Fetch live weather for location
    live_w = fetch_live_weather(soil_test.location)

    weather = WeatherData.objects.create(
        location=soil_test.location,
        date=date.today(),
        season=live_w['season'],
        temp_max=live_w['temp_max'],
        temp_min=live_w['temp_min'],
        temp_avg=live_w['temp_avg'],
        rainfall_mm=live_w['rainfall_mm'],
        past_rainfall_7d_mm=live_w['past_rainfall_7d_mm'],
        forecast_rainfall_7d_mm=live_w['forecast_rainfall_7d_mm'],
        forecast_summary=live_w['forecast_summary'],
        weather_source=live_w['weather_source'],
        humidity_percent=live_w['humidity_percent'],
        wind_speed_kmh=live_w['wind_speed_kmh'],
        sunshine_hours=live_w['sunshine_hours'],
        is_forecast=True,
    )

    return redirect('soil_engine:results', soil_id=soil_id, weather_id=weather.id)


def results(request, soil_id, weather_id):
    """
    Results page — runs the Soil Engine with crop age/stage & geo-source intelligence.
    """
    soil_test = get_object_or_404(SoilTest, id=soil_id)
    weather = get_object_or_404(WeatherData, id=weather_id)
    history = FertilizationHistory.objects.filter(soil_test=soil_test)

    # Allow interactive switching of target crop, crop age, and growth stage via query params
    target_crop = request.GET.get('crop', soil_test.selected_crop or None)

    crop_age_param = request.GET.get('age')
    if crop_age_param is not None:
        try:
            crop_age_years = float(crop_age_param)
        except ValueError:
            crop_age_years = soil_test.crop_age_years
    else:
        crop_age_years = soil_test.crop_age_years

    growth_stage = request.GET.get('stage', soil_test.growth_stage or 'basal')

    # Run the Soil Engine
    engine = SoilEngine(
        soil_test=soil_test,
        weather_data=weather,
        fertilization_history=list(history),
        target_crop=target_crop,
        crop_age_years=crop_age_years,
        growth_stage=growth_stage,
    )

    # Get results
    crop_suggestions = engine.get_crop_suggestions(top_n=8)

    if not target_crop and crop_suggestions:
        target_crop = crop_suggestions[0]['crop_name']

    # Current target crop data
    target_crop_data = CROP_DATABASE.get(target_crop, {})
    is_plantation = (target_crop_data.get('crop_type') == 'plantation')

    fert_plan = engine.get_fertilization_plan(target_crop, crop_age_years, growth_stage)
    derivatives = engine.get_derivatives(target_crop, crop_age_years, growth_stage)

    # Calculate totals
    total_fert_cost = sum(f['cost_per_ha'] for f in fert_plan)
    total_n = sum(f['n_delivered'] for f in fert_plan)
    total_p = sum(f['p_delivered'] for f in fert_plan)
    total_k = sum(f['k_delivered'] for f in fert_plan)

    # Persist results to database
    _save_results(soil_test, weather, crop_suggestions, fert_plan, derivatives)

    context = {
        'soil_test': soil_test,
        'weather': weather,
        'history': history,
        'crop_suggestions': crop_suggestions,
        'target_crop': target_crop,
        'target_crop_data': target_crop_data,
        'is_plantation': is_plantation,
        'crop_age_years': crop_age_years,
        'growth_stage': growth_stage,
        'fert_plan': fert_plan,
        'total_fert_cost': total_fert_cost,
        'total_n': total_n,
        'total_p': total_p,
        'total_k': total_k,
        'derivatives': derivatives,
        'all_crops': CROP_DATABASE,
        'page_title': 'Soil Engine Intelligence Results',
        'crop_suggestions_json': json.dumps(crop_suggestions),
        'fert_plan_json': json.dumps(fert_plan, default=str),
    }
    return render(request, 'soil_engine/results.html', context)


def _save_results(soil_test, weather, crop_suggestions, fert_plan, derivatives):
    """Persist Soil Engine results to database."""
    # Save crop suggestions
    CropSuggestion.objects.filter(soil_test=soil_test).delete()
    for s in crop_suggestions:
        CropSuggestion.objects.create(
            soil_test=soil_test,
            weather_data=weather,
            crop_name=s['crop_name'],
            suitability_score=s['suitability_score'],
            reason=s['reason'],
            expected_yield_tonnes_per_ha=s['expected_yield'],
            season=s['season'],
        )

    # Save fertilization cycles
    FertilizationCycle.objects.filter(soil_test=soil_test).delete()
    for f in fert_plan:
        FertilizationCycle.objects.create(
            soil_test=soil_test,
            crop_name=f.get('crop_name', ''),
            crop_age_or_stage=f.get('crop_age_or_stage', ''),
            fertilizer_type=f['fertilizer_type'],
            quantity_kg_per_ha=f['quantity_kg_per_ha'],
            application_stage=f['application_stage'],
            recommended_date=f.get('recommended_date'),
            nitrogen_delivered=f['n_delivered'],
            phosphorus_delivered=f['p_delivered'],
            potassium_delivered=f['k_delivered'],
            estimated_cost_per_ha=f['cost_per_ha'],
            notes=f.get('notes', ''),
        )

    # Save derivative forecasts
    DerivativeForecast.objects.filter(soil_test=soil_test).delete()
    for key, deriv in derivatives.items():
        if isinstance(deriv, dict) and 'type' in deriv:
            DerivativeForecast.objects.create(
                soil_test=soil_test,
                forecast_type=deriv['type'],
                title=deriv['title'],
                value=deriv.get('value', 0) if isinstance(deriv.get('value'), (int, float)) else 0,
                unit=deriv.get('unit', ''),
                confidence_percent=deriv.get('confidence', 75),
                details=deriv.get('details', ''),
            )


def soil_test_list(request):
    """List all soil tests."""
    tests = SoilTest.objects.all()
    context = {
        'tests': tests,
        'page_title': 'All Soil Tests & Geo Reports',
    }
    return render(request, 'soil_engine/soil_test_list.html', context)


def soil_test_detail(request, soil_id):
    """View details of a specific soil test."""
    soil_test = get_object_or_404(SoilTest, id=soil_id)
    suggestions = CropSuggestion.objects.filter(soil_test=soil_test)
    cycles = FertilizationCycle.objects.filter(soil_test=soil_test)
    forecasts = DerivativeForecast.objects.filter(soil_test=soil_test)
    history = FertilizationHistory.objects.filter(soil_test=soil_test)

    context = {
        'soil_test': soil_test,
        'suggestions': suggestions,
        'cycles': cycles,
        'forecasts': forecasts,
        'history': history,
        'page_title': f'Soil Test: {soil_test.sample_id}',
    }
    return render(request, 'soil_engine/soil_test_detail.html', context)


# ---- API ENDPOINTS ----

@require_http_methods(["GET"])
def api_geo_soil_lookup(request):
    """
    Public Geo Soil API lookup endpoint.
    Accepts: location, taluk, district, lat, lon
    Returns: Soil parameters, data source attribution, confidence
    """
    location = request.GET.get('location', '').strip()
    taluk = request.GET.get('taluk', '').strip()
    district = request.GET.get('district', '').strip()
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    lat_f = float(lat) if lat else None
    lon_f = float(lon) if lon else None

    data = fetch_geo_soil_data(
        location_query=location,
        taluk=taluk or None,
        district=district or None,
        lat=lat_f,
        lon=lon_f,
    )
    return JsonResponse(data)


@require_http_methods(["GET"])
def api_geo_weather(request):
    """
    Public Geo Weather API lookup endpoint using Open-Meteo.
    Accepts: location, lat, lon
    Returns: Recent rainfall (7d), Forecast rainfall (7d), temps, wind, advisory
    """
    location = request.GET.get('location', '').strip()
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    lat_f = float(lat) if lat else None
    lon_f = float(lon) if lon else None

    data = fetch_live_weather(
        location_query=location,
        lat=lat_f,
        lon=lon_f,
    )
    return JsonResponse(data)


@require_http_methods(["GET"])
def api_crop_database(request):
    """API endpoint to get the crop database."""
    return JsonResponse({'crops': CROP_DATABASE})


@require_http_methods(["GET"])
def api_fertilizer_database(request):
    """API endpoint to get the fertilizer database."""
    return JsonResponse({'fertilizers': FERTILIZER_DATABASE})
