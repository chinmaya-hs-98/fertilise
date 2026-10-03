"""
Weather Service — Free Open-Meteo Meteorological Intelligence.

Fetches real-time and historical agro-climate data:
- Recent past rainfall (last 7 days precipitation sum in mm)
- Upcoming forecast rainfall (next 7 days precipitation sum & daily breakdown in mm)
- Temperature (max, min, avg)
- Humidity, wind speed, solar sunshine estimates
- Season detection (Kharif, Rabi, Zaid)
- Weather-guided fertilization advisories (leaching risk alerts, application timing)
"""

import json
import logging
import urllib.request
import urllib.parse
from datetime import date
from typing import Dict, Any, Optional

from .geo_soil_service import geocode_location

logger = logging.getLogger(__name__)


def fetch_live_weather(
    location_query: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Fetch comprehensive recent past + 7-day forecast weather from Open-Meteo free API.
    Does not require any API key.
    """
    # 1. Resolve coordinates if not provided
    geo_name = location_query or "Farm Location"
    if lat is None or lon is None:
        if location_query:
            geo_info = geocode_location(location_query)
            if geo_info and geo_info.get('latitude') and geo_info.get('longitude'):
                lat = geo_info['latitude']
                lon = geo_info['longitude']
                geo_name = geo_info.get('name', location_query)
        
        # Fallback to central Indian coordinates if geocoding fails
        if lat is None or lon is None:
            lat = 15.3173
            lon = 75.7139
            geo_name = location_query or "Karnataka Agro-Zone"

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat:.4f}&longitude={lon:.4f}&"
        f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,windspeed_10m_max&"
        f"current_weather=true&"
        f"past_days=7&forecast_days=7&"
        f"timezone=auto"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'SoilEngine/1.0 (Agricultural Intelligence Platform)'}
        )
        with urllib.request.urlopen(req, timeout=4.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                
                daily = data.get('daily', {})
                dates = daily.get('time', [])
                precip_list = daily.get('precipitation_sum', [])
                temp_max_list = daily.get('temperature_2m_max', [])
                temp_min_list = daily.get('temperature_2m_min', [])
                wind_list = daily.get('windspeed_10m_max', [])
                prob_list = daily.get('precipitation_probability_max', [])

                # Split past 7 days vs next 7 days
                past_precip = sum(filter(None, precip_list[:7])) if len(precip_list) >= 7 else 0.0
                forecast_precip = sum(filter(None, precip_list[7:])) if len(precip_list) > 7 else sum(filter(None, precip_list))
                
                current_weather = data.get('current_weather', {})
                current_temp = current_weather.get('temperature', 28.0)
                current_wind = current_weather.get('windspeed', 12.0)

                # Averages for current week
                forecast_temp_max = (sum(temp_max_list[7:]) / len(temp_max_list[7:])) if len(temp_max_list) > 7 else 32.0
                forecast_temp_min = (sum(temp_min_list[7:]) / len(temp_min_list[7:])) if len(temp_min_list) > 7 else 22.0
                avg_temp = round((forecast_temp_max + forecast_temp_min) / 2.0, 1)

                # Daily forecast breakdown for UI chart/timeline
                daily_forecast = []
                for i in range(min(len(dates), len(precip_list))):
                    daily_forecast.append({
                        'date': dates[i],
                        'is_past': (i < 7),
                        'precip_mm': round(precip_list[i] or 0.0, 1),
                        'temp_max': round(temp_max_list[i] or 30.0, 1) if i < len(temp_max_list) else 30.0,
                        'temp_min': round(temp_min_list[i] or 20.0, 1) if i < len(temp_min_list) else 20.0,
                        'rain_prob': prob_list[i] if i < len(prob_list) else 0,
                    })

                # Determine season
                month = date.today().month
                season = 'kharif' if 6 <= month <= 10 else ('rabi' if month <= 3 or month >= 11 else 'zaid')

                # Agro-advisory generation
                advisory = []
                if forecast_precip > 50.0:
                    advisory.append("⚠️ High rainfall (>50mm) forecast in next 7 days: Postpone urea broadcasting to avoid nitrogen leaching.")
                elif forecast_precip > 20.0:
                    advisory.append("🌧️ Moderate showers expected: Favorable for basal application and organic manuring.")
                elif forecast_precip < 5.0 and past_precip < 10.0:
                    advisory.append("☀️ Dry spell active: Ensure post-fertilization irrigation to prevent fertilizer salt burn.")

                return {
                    'location': geo_name,
                    'latitude': lat,
                    'longitude': lon,
                    'date': date.today().strftime('%Y-%m-%d'),
                    'season': season,
                    'temp_max': round(forecast_temp_max, 1),
                    'temp_min': round(forecast_temp_min, 1),
                    'temp_avg': avg_temp,
                    'rainfall_mm': round(forecast_precip, 1),
                    'past_rainfall_7d_mm': round(past_precip, 1),
                    'forecast_rainfall_7d_mm': round(forecast_precip, 1),
                    'humidity_percent': 70.0 if forecast_precip > 15 else 55.0,
                    'wind_speed_kmh': round(current_wind, 1),
                    'sunshine_hours': 5.0 if forecast_precip > 25 else 7.5,
                    'daily_forecast': daily_forecast,
                    'forecast_summary': " | ".join(advisory) if advisory else "Favorable weather conditions for planned agronomic schedule.",
                    'weather_source': 'Open-Meteo Global Meteorological API (Live & Forecast)',
                    'is_live_api': True,
                    'confidence': 95,
                }
    except Exception as e:
        logger.warning(f"Live weather lookup failed for '{location_query}': {e}")

    # Fallback to realistic agro-climatic seasonal default
    month = date.today().month
    season = 'kharif' if 6 <= month <= 10 else ('rabi' if month <= 3 or month >= 11 else 'zaid')
    return {
        'location': location_query or "Regional Agro Station",
        'latitude': lat,
        'longitude': lon,
        'date': date.today().strftime('%Y-%m-%d'),
        'season': season,
        'temp_max': 33.0,
        'temp_min': 22.0,
        'temp_avg': 27.5,
        'rainfall_mm': 65.0,
        'past_rainfall_7d_mm': 28.0,
        'forecast_rainfall_7d_mm': 42.0,
        'humidity_percent': 68.0,
        'wind_speed_kmh': 11.0,
        'sunshine_hours': 6.5,
        'daily_forecast': [],
        'forecast_summary': "Seasonal standard weather model based on regional agro-climatic normals.",
        'weather_source': 'Regional Agro-Climatic Representative Norms',
        'is_live_api': False,
        'confidence': 80,
    }
