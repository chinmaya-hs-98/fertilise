"""
Soil Engine Core — Advanced Agronomic Intelligence Engine.

Implements realistic agronomic logic based on:
- Indian Council of Agricultural Research (ICAR) recommendations
- Central Plantation Crops Research Institute (CPCRI) guidelines
- National Horticulture Board & State Agricultural Universities (UAS Dharwad, TNAU, MPKV, PAU)
- Indian soil testing standards (N-P-K critical limits, pH, OC, micronutrients)

Inputs:
  - Soil Test Data (Manual lab test or Regional Free API fallback)
  - Weather Data (Temperature, Rainfall, Humidity, Season)
  - Fertilization History (Residual feedback loop)
  - Target Crop Selection (Optional: Field / Seasonal vs Plantation / Perennial)
  - Crop Age in Years (for Plantations) / Growth Stage (for Seasonal Crops)

Outputs:
  - Crop Suitability Suggestions & Revenue Estimates
  - Tailored Next Fertilization Cycle (Age-adjusted for plantations, Stage-adjusted for seasonal crops)
  - Multi-tier Derivative Forecasts (Yield, Fertilizer, Equipment, Labor, Sub-derivatives)
"""

from datetime import date, timedelta
import math
from typing import List, Dict, Any, Optional


# =============================================================================
# EXTENDED CROP DATABASE
# Supports Seasonal / Field Crops and Plantation / Perennial Crops
# =============================================================================

CROP_DATABASE = {
    # -------------------------------------------------------------------------
    # PLANTATIONS & PERENNIALS (Age-based nutrient scaling in Years)
    # -------------------------------------------------------------------------
    'Arecanut (Betel Nut)': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],  # Perennial year-round
        'ph_range': (5.2, 7.5),
        'ideal_ph': 6.2,
        'adult_n_per_plant_g': 100,  # grams/palm/year
        'adult_p_per_plant_g': 40,
        'adult_k_per_plant_g': 140,
        'plants_per_ha': 1300,       # Spacing 2.7m x 2.7m (~1300 palms/ha)
        'n_requirement': 130,        # adult kg/ha
        'p_requirement': 52,
        'k_requirement': 182,
        'water_need': 'high',
        'temp_range': (15, 38),
        'ideal_temp': 28,
        'rainfall_min': 150,
        'soil_types': ['laterite', 'red', 'clay_loam', 'alluvial'],
        'duration_days': 365,
        'bearing_age_years': 4,
        'age_scaling': {
            1: 0.33,  # 1st year seedling: 1/3 dose
            2: 0.66,  # 2nd year: 2/3 dose
            3: 0.85,  # 3rd year: 85% dose
            4: 1.00,  # 4+ years: Full adult bearing dose
        },
        'splits': [
            {'name': 'Pre-Monsoon Dose (May-June)', 'n_pct': 0.33, 'p_pct': 0.50, 'k_pct': 0.33, 'days_offset': 10},
            {'name': 'Post-Monsoon Dose (Sept-Oct)', 'n_pct': 0.67, 'p_pct': 0.50, 'k_pct': 0.67, 'days_offset': 75},
        ],
        'avg_yield': 2.5,        # tonnes of chali (cured nuts)/ha
        'max_yield': 4.5,
        'msp_per_quintal': 45000, # ₹/quintal
    },

    'Coconut': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],
        'ph_range': (5.2, 8.0),
        'ideal_ph': 6.5,
        'adult_n_per_plant_g': 500,  # grams/palm/year
        'adult_p_per_plant_g': 320,
        'adult_k_per_plant_g': 1200,
        'plants_per_ha': 175,        # 7.5m x 7.5m spacing
        'n_requirement': 87.5,
        'p_requirement': 56.0,
        'k_requirement': 210.0,
        'water_need': 'high',
        'temp_range': (20, 36),
        'ideal_temp': 27,
        'rainfall_min': 120,
        'soil_types': ['laterite', 'alluvial', 'red', 'sandy_loam', 'clay_loam'],
        'duration_days': 365,
        'bearing_age_years': 5,
        'age_scaling': {
            1: 0.25,
            2: 0.50,
            3: 0.75,
            4: 1.00,
        },
        'splits': [
            {'name': 'Pre-Monsoon Dose (May-June)', 'n_pct': 0.33, 'p_pct': 0.50, 'k_pct': 0.33, 'days_offset': 10},
            {'name': 'Post-Monsoon Dose (Sept-Oct)', 'n_pct': 0.67, 'p_pct': 0.50, 'k_pct': 0.67, 'days_offset': 75},
        ],
        'avg_yield': 12.0,       # 12,000 nuts / ha (~12 tonnes)
        'max_yield': 20.0,
        'msp_per_quintal': 12000,
    },

    'Coffee (Arabica / Robusta)': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],
        'ph_range': (5.5, 6.8),
        'ideal_ph': 6.0,
        'adult_n_per_plant_g': 60,
        'adult_p_per_plant_g': 45,
        'adult_k_per_plant_g': 60,
        'plants_per_ha': 2500,       # 2m x 2m spacing
        'n_requirement': 150,
        'p_requirement': 110,
        'k_requirement': 150,
        'water_need': 'high',
        'temp_range': (15, 30),
        'ideal_temp': 23,
        'rainfall_min': 120,
        'soil_types': ['laterite', 'red', 'loamy'],
        'duration_days': 365,
        'bearing_age_years': 3,
        'age_scaling': {
            1: 0.30,
            2: 0.60,
            3: 1.00,
        },
        'splits': [
            {'name': 'Pre-Blossom (March)', 'n_pct': 0.25, 'p_pct': 0.25, 'k_pct': 0.25, 'days_offset': 10},
            {'name': 'Post-Blossom / Pre-Monsoon (May)', 'n_pct': 0.25, 'p_pct': 0.25, 'k_pct': 0.25, 'days_offset': 45},
            {'name': 'Mid-Monsoon (August)', 'n_pct': 0.25, 'p_pct': 0.25, 'k_pct': 0.25, 'days_offset': 90},
            {'name': 'Post-Monsoon (October-Nov)', 'n_pct': 0.25, 'p_pct': 0.25, 'k_pct': 0.25, 'days_offset': 135},
        ],
        'avg_yield': 1.8,        # tonnes clean coffee/ha
        'max_yield': 3.2,
        'msp_per_quintal': 28000,
    },

    'Rubber': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],
        'ph_range': (4.5, 6.5),
        'ideal_ph': 5.5,
        'adult_n_per_plant_g': 80,
        'adult_p_per_plant_g': 40,
        'adult_k_per_plant_g': 60,
        'plants_per_ha': 450,
        'n_requirement': 36,
        'p_requirement': 18,
        'k_requirement': 27,
        'water_need': 'high',
        'temp_range': (20, 34),
        'ideal_temp': 28,
        'rainfall_min': 160,
        'soil_types': ['laterite', 'red', 'clay_loam'],
        'duration_days': 365,
        'bearing_age_years': 7,
        'age_scaling': {
            1: 0.20,
            2: 0.35,
            3: 0.50,
            4: 0.70,
            5: 0.85,
            6: 0.95,
            7: 1.00,
        },
        'splits': [
            {'name': 'Pre-Monsoon (April-May)', 'n_pct': 0.50, 'p_pct': 0.50, 'k_pct': 0.50, 'days_offset': 15},
            {'name': 'Post-Monsoon (Sept-Oct)', 'n_pct': 0.50, 'p_pct': 0.50, 'k_pct': 0.50, 'days_offset': 90},
        ],
        'avg_yield': 2.0,        # tonnes dry rubber/ha
        'max_yield': 3.5,
        'msp_per_quintal': 18000,
    },

    'Mango Orchard': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],
        'ph_range': (5.5, 7.5),
        'ideal_ph': 6.5,
        'adult_n_per_plant_g': 1000,
        'adult_p_per_plant_g': 500,
        'adult_k_per_plant_g': 1000,
        'plants_per_ha': 100,        # 10m x 10m spacing
        'n_requirement': 100,
        'p_requirement': 50,
        'k_requirement': 100,
        'water_need': 'medium',
        'temp_range': (20, 42),
        'ideal_temp': 28,
        'rainfall_min': 60,
        'soil_types': ['alluvial', 'red', 'loamy', 'laterite'],
        'duration_days': 365,
        'bearing_age_years': 5,
        'age_scaling': {
            1: 0.15,
            2: 0.30,
            3: 0.50,
            4: 0.75,
            5: 1.00,
        },
        'splits': [
            {'name': 'Post-Harvest Dose (June-July)', 'n_pct': 0.60, 'p_pct': 1.00, 'k_pct': 0.50, 'days_offset': 15},
            {'name': 'Pre-Flowering / Fruit Set Dose (Dec-Jan)', 'n_pct': 0.40, 'p_pct': 0.0, 'k_pct': 0.50, 'days_offset': 90},
        ],
        'avg_yield': 10.0,       # tonnes/ha
        'max_yield': 20.0,
        'msp_per_quintal': 4000,
    },

    'Black Pepper (Intercrop/Pure)': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],
        'ph_range': (5.0, 6.5),
        'ideal_ph': 5.8,
        'adult_n_per_plant_g': 140,
        'adult_p_per_plant_g': 55,
        'adult_k_per_plant_g': 270,
        'plants_per_ha': 1100,
        'n_requirement': 154,
        'p_requirement': 60,
        'k_requirement': 297,
        'water_need': 'high',
        'temp_range': (18, 35),
        'ideal_temp': 28,
        'rainfall_min': 150,
        'soil_types': ['laterite', 'red', 'clay_loam'],
        'duration_days': 365,
        'bearing_age_years': 3,
        'age_scaling': {
            1: 0.33,
            2: 0.66,
            3: 1.00,
        },
        'splits': [
            {'name': 'Pre-Monsoon (May-June)', 'n_pct': 0.33, 'p_pct': 0.50, 'k_pct': 0.33, 'days_offset': 15},
            {'name': 'Post-Monsoon (Aug-Sept)', 'n_pct': 0.67, 'p_pct': 0.50, 'k_pct': 0.67, 'days_offset': 75},
        ],
        'avg_yield': 1.5,
        'max_yield': 3.0,
        'msp_per_quintal': 58000,
    },

    'Banana': {
        'category': 'Plantation',
        'crop_type': 'plantation',
        'season': ['kharif', 'rabi', 'zaid'],
        'ph_range': (6.0, 7.5),
        'ideal_ph': 6.5,
        'adult_n_per_plant_g': 200,
        'adult_p_per_plant_g': 50,
        'adult_k_per_plant_g': 300,
        'plants_per_ha': 2500,       # 1.8m x 1.8m spacing
        'n_requirement': 500,
        'p_requirement': 125,
        'k_requirement': 750,
        'water_need': 'high',
        'temp_range': (18, 38),
        'ideal_temp': 27,
        'rainfall_min': 100,
        'soil_types': ['alluvial', 'clay_loam', 'loamy', 'black'],
        'duration_days': 330,
        'bearing_age_years': 1,
        'age_scaling': {
            1: 1.00,
        },
        'splits': [
            {'name': '30 Days After Planting', 'n_pct': 0.25, 'p_pct': 0.50, 'k_pct': 0.20, 'days_offset': 30},
            {'name': '75 Days (Vegetative Peak)', 'n_pct': 0.35, 'p_pct': 0.50, 'k_pct': 0.30, 'days_offset': 75},
            {'name': '150 Days (Shooting / Bunch Emergence)', 'n_pct': 0.40, 'p_pct': 0.0, 'k_pct': 0.50, 'days_offset': 150},
        ],
        'avg_yield': 60.0,
        'max_yield': 90.0,
        'msp_per_quintal': 1800,
    },

    # -------------------------------------------------------------------------
    # FIELD & SEASONAL CROPS (Growth Stage-based nutrient splits)
    # -------------------------------------------------------------------------
    'Rice (Paddy)': {
        'category': 'Cereal',
        'crop_type': 'seasonal',
        'season': ['kharif'],
        'ph_range': (5.0, 7.5),
        'ideal_ph': 6.5,
        'n_requirement': 120,
        'p_requirement': 60,
        'k_requirement': 60,
        'water_need': 'high',
        'temp_range': (20, 37),
        'ideal_temp': 28,
        'rainfall_min': 100,
        'soil_types': ['alluvial', 'clay', 'loamy', 'clay_loam'],
        'duration_days': 120,
        'stage_ratios': {
            'basal': {'n': 0.33, 'p': 1.00, 'k': 0.50, 'name': 'Basal (Transplanting)'},
            'vegetative': {'n': 0.33, 'p': 0.0, 'k': 0.0, 'name': 'Active Tillering (21-25 DAT)'},
            'flowering': {'n': 0.34, 'p': 0.0, 'k': 0.50, 'name': 'Panicle Initiation (45-50 DAT)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Grain Filling (Foliar Micronutrients)'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Maturity (Stop Fertilization)'},
        },
        'avg_yield': 5.0,
        'max_yield': 8.0,
        'msp_per_quintal': 2183,
    },

    'Wheat': {
        'category': 'Cereal',
        'crop_type': 'seasonal',
        'season': ['rabi'],
        'ph_range': (6.0, 7.5),
        'ideal_ph': 6.8,
        'n_requirement': 120,
        'p_requirement': 60,
        'k_requirement': 40,
        'water_need': 'medium',
        'temp_range': (10, 25),
        'ideal_temp': 20,
        'rainfall_min': 40,
        'soil_types': ['alluvial', 'loamy', 'clay_loam', 'sandy_loam'],
        'duration_days': 135,
        'stage_ratios': {
            'basal': {'n': 0.50, 'p': 1.00, 'k': 1.00, 'name': 'Basal (Sowing)'},
            'vegetative': {'n': 0.25, 'p': 0.0, 'k': 0.0, 'name': 'Crown Root Initiation / Tillering (21 DAS)'},
            'flowering': {'n': 0.25, 'p': 0.0, 'k': 0.0, 'name': 'Jointing / Booting (45 DAS)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Milk / Dough Stage'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Maturity'},
        },
        'avg_yield': 4.5,
        'max_yield': 7.0,
        'msp_per_quintal': 2275,
    },

    'Maize': {
        'category': 'Cereal',
        'crop_type': 'seasonal',
        'season': ['kharif', 'rabi'],
        'ph_range': (5.5, 7.5),
        'ideal_ph': 6.5,
        'n_requirement': 150,
        'p_requirement': 60,
        'k_requirement': 40,
        'water_need': 'medium',
        'temp_range': (18, 35),
        'ideal_temp': 27,
        'rainfall_min': 60,
        'soil_types': ['loamy', 'sandy_loam', 'alluvial'],
        'duration_days': 100,
        'stage_ratios': {
            'basal': {'n': 0.33, 'p': 1.00, 'k': 1.00, 'name': 'Basal (Sowing)'},
            'vegetative': {'n': 0.33, 'p': 0.0, 'k': 0.0, 'name': 'Knee High Stage (30 DAS)'},
            'flowering': {'n': 0.34, 'p': 0.0, 'k': 0.0, 'name': 'Tasseling & Silking (50 DAS)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Cob Filling'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Maturity'},
        },
        'avg_yield': 6.0,
        'max_yield': 10.0,
        'msp_per_quintal': 2090,
    },

    'Cotton': {
        'category': 'Cash Crop',
        'crop_type': 'seasonal',
        'season': ['kharif'],
        'ph_range': (6.0, 8.0),
        'ideal_ph': 7.0,
        'n_requirement': 120,
        'p_requirement': 60,
        'k_requirement': 60,
        'water_need': 'medium',
        'temp_range': (21, 38),
        'ideal_temp': 30,
        'rainfall_min': 50,
        'soil_types': ['black', 'alluvial', 'loamy', 'clay_loam'],
        'duration_days': 180,
        'stage_ratios': {
            'basal': {'n': 0.25, 'p': 1.00, 'k': 0.50, 'name': 'Basal (Sowing)'},
            'vegetative': {'n': 0.35, 'p': 0.0, 'k': 0.0, 'name': 'Squaring Stage (45 DAS)'},
            'flowering': {'n': 0.40, 'p': 0.0, 'k': 0.50, 'name': 'Flowering & Boll Formation (75 DAS)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Boll Bursting'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Maturity & Picking'},
        },
        'avg_yield': 2.0,
        'max_yield': 4.0,
        'msp_per_quintal': 6620,
    },

    'Sugarcane': {
        'category': 'Cash Crop',
        'crop_type': 'seasonal',
        'season': ['kharif', 'zaid'],
        'ph_range': (6.0, 8.0),
        'ideal_ph': 6.5,
        'n_requirement': 250,
        'p_requirement': 100,
        'k_requirement': 120,
        'water_need': 'high',
        'temp_range': (20, 40),
        'ideal_temp': 30,
        'rainfall_min': 80,
        'soil_types': ['alluvial', 'loamy', 'clay_loam', 'black'],
        'duration_days': 365,
        'stage_ratios': {
            'basal': {'n': 0.20, 'p': 1.00, 'k': 0.33, 'name': 'At Planting'},
            'vegetative': {'n': 0.40, 'p': 0.0, 'k': 0.33, 'name': 'Tillering / Formative (45-60 DAP)'},
            'flowering': {'n': 0.40, 'p': 0.0, 'k': 0.34, 'name': 'Grand Growth / Earthing Up (90-120 DAP)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Sucrose Accumulation'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Ripening'},
        },
        'avg_yield': 70.0,
        'max_yield': 120.0,
        'msp_per_quintal': 315,
    },

    'Chickpea (Gram)': {
        'category': 'Pulse',
        'crop_type': 'seasonal',
        'season': ['rabi'],
        'ph_range': (6.0, 8.0),
        'ideal_ph': 7.0,
        'n_requirement': 20,
        'p_requirement': 60,
        'k_requirement': 20,
        'water_need': 'low',
        'temp_range': (10, 30),
        'ideal_temp': 22,
        'rainfall_min': 20,
        'soil_types': ['loamy', 'clay_loam', 'black', 'alluvial'],
        'duration_days': 100,
        'stage_ratios': {
            'basal': {'n': 1.00, 'p': 1.00, 'k': 1.00, 'name': 'Basal (At Sowing)'},
            'vegetative': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Vegetative (Rhizobium Active)'},
            'flowering': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Flowering (Foliar Urea/DAP 2%)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Pod Development'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Maturity'},
        },
        'avg_yield': 1.5,
        'max_yield': 3.0,
        'msp_per_quintal': 5440,
    },

    'Groundnut': {
        'category': 'Oilseed',
        'crop_type': 'seasonal',
        'season': ['kharif'],
        'ph_range': (6.0, 7.0),
        'ideal_ph': 6.5,
        'n_requirement': 25,
        'p_requirement': 50,
        'k_requirement': 45,
        'water_need': 'medium',
        'temp_range': (22, 35),
        'ideal_temp': 28,
        'rainfall_min': 50,
        'soil_types': ['sandy_loam', 'loamy', 'red'],
        'duration_days': 110,
        'stage_ratios': {
            'basal': {'n': 0.50, 'p': 1.00, 'k': 0.50, 'name': 'Basal (Sowing)'},
            'vegetative': {'n': 0.50, 'p': 0.0, 'k': 0.50, 'name': 'Pegging / Flowering (30-35 DAS)'},
            'flowering': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Pod Development (Gypsum @ 400kg/ha)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Pod Filling'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Maturity'},
        },
        'avg_yield': 2.0,
        'max_yield': 3.5,
        'msp_per_quintal': 6377,
    },

    'Potato': {
        'category': 'Vegetable',
        'crop_type': 'seasonal',
        'season': ['rabi'],
        'ph_range': (5.0, 6.5),
        'ideal_ph': 5.5,
        'n_requirement': 180,
        'p_requirement': 100,
        'k_requirement': 150,
        'water_need': 'high',
        'temp_range': (10, 25),
        'ideal_temp': 18,
        'rainfall_min': 40,
        'soil_types': ['sandy_loam', 'loamy', 'alluvial'],
        'duration_days': 90,
        'stage_ratios': {
            'basal': {'n': 0.50, 'p': 1.00, 'k': 0.50, 'name': 'At Planting'},
            'vegetative': {'n': 0.50, 'p': 0.0, 'k': 0.50, 'name': 'Earthing Up (30-35 DAP)'},
            'flowering': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Tuber Bulking'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Tuber Maturation'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Haulm Cutting / Harvest'},
        },
        'avg_yield': 25.0,
        'max_yield': 45.0,
        'msp_per_quintal': 1500,
    },

    'Tomato': {
        'category': 'Vegetable',
        'crop_type': 'seasonal',
        'season': ['rabi', 'kharif'],
        'ph_range': (6.0, 7.0),
        'ideal_ph': 6.5,
        'n_requirement': 120,
        'p_requirement': 80,
        'k_requirement': 80,
        'water_need': 'medium',
        'temp_range': (15, 32),
        'ideal_temp': 25,
        'rainfall_min': 40,
        'soil_types': ['loamy', 'sandy_loam', 'red'],
        'duration_days': 90,
        'stage_ratios': {
            'basal': {'n': 0.33, 'p': 1.00, 'k': 0.33, 'name': 'Basal (Transplanting)'},
            'vegetative': {'n': 0.33, 'p': 0.0, 'k': 0.33, 'name': 'Vegetative Growth (20-25 DAT)'},
            'flowering': {'n': 0.34, 'p': 0.0, 'k': 0.34, 'name': 'Flowering & Fruit Setting (45 DAT)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Fruit Development'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Harvesting Flushes'},
        },
        'avg_yield': 30.0,
        'max_yield': 60.0,
        'msp_per_quintal': 2000,
    },

    'Chilli': {
        'category': 'Spice',
        'crop_type': 'seasonal',
        'season': ['kharif', 'rabi'],
        'ph_range': (6.0, 7.0),
        'ideal_ph': 6.5,
        'n_requirement': 100,
        'p_requirement': 50,
        'k_requirement': 50,
        'water_need': 'medium',
        'temp_range': (20, 35),
        'ideal_temp': 28,
        'rainfall_min': 40,
        'soil_types': ['loamy', 'sandy_loam', 'black', 'red'],
        'duration_days': 150,
        'stage_ratios': {
            'basal': {'n': 0.33, 'p': 1.00, 'k': 0.50, 'name': 'Basal (Transplanting)'},
            'vegetative': {'n': 0.33, 'p': 0.0, 'k': 0.0, 'name': 'Vegetative Branching (30 DAT)'},
            'flowering': {'n': 0.34, 'p': 0.0, 'k': 0.50, 'name': 'Flowering & Fruit Initiation (60 DAT)'},
            'fruiting': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Fruit Development'},
            'maturity': {'n': 0.0, 'p': 0.0, 'k': 0.0, 'name': 'Picking Stage'},
        },
        'avg_yield': 2.0,
        'max_yield': 5.0,
        'msp_per_quintal': 12000,
    },
}


# =============================================================================
# FERTILIZER DATABASE
# =============================================================================

FERTILIZER_DATABASE = {
    'urea': {
        'name': 'Urea',
        'n_percent': 46.0, 'p_percent': 0, 'k_percent': 0,
        'price_per_kg': 5.36,
        'description': 'Primary nitrogen source, most widely used',
    },
    'dap': {
        'name': 'DAP (Diammonium Phosphate)',
        'n_percent': 18.0, 'p_percent': 46.0, 'k_percent': 0,
        'price_per_kg': 27.0,
        'description': 'Balanced NP fertilizer for basal application',
    },
    'mop': {
        'name': 'MOP (Muriate of Potash)',
        'n_percent': 0, 'p_percent': 0, 'k_percent': 60.0,
        'price_per_kg': 16.75,
        'description': 'Primary potassium source',
    },
    'ssp': {
        'name': 'SSP (Single Super Phosphate)',
        'n_percent': 0, 'p_percent': 16.0, 'k_percent': 0,
        'price_per_kg': 8.0,
        'description': 'Phosphorus + Sulphur source',
    },
    'npk_10_26_26': {
        'name': 'NPK 10:26:26',
        'n_percent': 10.0, 'p_percent': 26.0, 'k_percent': 26.0,
        'price_per_kg': 24.0,
        'description': 'Complex fertilizer for balanced nutrition',
    },
    'npk_12_32_16': {
        'name': 'NPK 12:32:16',
        'n_percent': 12.0, 'p_percent': 32.0, 'k_percent': 16.0,
        'price_per_kg': 26.0,
        'description': 'Phosphorus-rich complex fertilizer',
    },
    'npk_20_20_0': {
        'name': 'NPK 20:20:0',
        'n_percent': 20.0, 'p_percent': 20.0, 'k_percent': 0,
        'price_per_kg': 22.0,
        'description': 'NP complex without potassium',
    },
    'npk_15_15_15': {
        'name': 'NPK 15:15:15',
        'n_percent': 15.0, 'p_percent': 15.0, 'k_percent': 15.0,
        'price_per_kg': 20.0,
        'description': 'Balanced complex fertilizer',
    },
    'ammonium_sulphate': {
        'name': 'Ammonium Sulphate',
        'n_percent': 20.6, 'p_percent': 0, 'k_percent': 0,
        'price_per_kg': 12.0,
        'description': 'Nitrogen + Sulphur source, ideal for acidic preference crops',
    },
    'zinc_sulphate': {
        'name': 'Zinc Sulphate',
        'n_percent': 0, 'p_percent': 0, 'k_percent': 0,
        'price_per_kg': 42.0,
        'description': 'Zinc micronutrient supplement',
    },
    'borax': {
        'name': 'Borax',
        'n_percent': 0, 'p_percent': 0, 'k_percent': 0,
        'price_per_kg': 60.0,
        'description': 'Boron micronutrient supplement',
    },
    'fym': {
        'name': 'Farm Yard Manure (FYM)',
        'n_percent': 0.5, 'p_percent': 0.2, 'k_percent': 0.5,
        'price_per_kg': 2.0,
        'description': 'Organic manure, improves soil structure & biology',
    },
    'vermicompost': {
        'name': 'Vermicompost',
        'n_percent': 1.5, 'p_percent': 0.4, 'k_percent': 1.5,
        'price_per_kg': 8.0,
        'description': 'Premium organic compost with balanced nutrients',
    },
    'gypsum': {
        'name': 'Agricultural Gypsum',
        'n_percent': 0, 'p_percent': 0, 'k_percent': 0,
        'price_per_kg': 4.5,
        'description': 'Calcium + Sulphur source for pod development and alkaline reclamation',
    },
    'neem_cake': {
        'name': 'Neem Cake',
        'n_percent': 5.0, 'p_percent': 1.0, 'k_percent': 1.4,
        'price_per_kg': 18.0,
        'description': 'Organic nitrogen inhibitor and root pest protectant',
    },
}


# =============================================================================
# SOIL ENGINE CORE
# =============================================================================

class SoilEngine:
    """
    Central processing engine that combines:
    1. Soil Test Data (Lab or Free Geo/Taluk API Fallback)
    2. Weather Data
    3. Fertilization History
    4. Target Crop + Crop Age in Years (Plantation) OR Growth Stage (Seasonal)
    """

    def __init__(
        self,
        soil_test,
        weather_data=None,
        fertilization_history=None,
        target_crop: Optional[str] = None,
        crop_age_years: Optional[float] = None,
        growth_stage: Optional[str] = None,
    ):
        self.soil = soil_test
        self.weather = weather_data
        self.history = fertilization_history or []
        self.season = self._determine_season()

        # Prioritize explicit parameters or model-stored values
        self.target_crop = target_crop or getattr(soil_test, 'selected_crop', None)
        self.crop_age_years = crop_age_years if crop_age_years is not None else getattr(soil_test, 'crop_age_years', None)
        self.growth_stage = growth_stage or getattr(soil_test, 'growth_stage', 'basal')

    def _determine_season(self):
        """Determine agricultural season."""
        if self.weather and self.weather.season:
            return self.weather.season

        month = date.today().month
        if 6 <= month <= 10:
            return 'kharif'
        elif 11 <= month <= 3:
            return 'rabi'
        else:
            return 'zaid'

    # ---- CROP SUGGESTIONS ----

    def get_crop_suggestions(self, top_n=10):
        """
        Generate crop suggestions based on soil, weather, and history.
        Prioritizes user-selected target crop if present.
        """
        suggestions = []

        for crop_name, crop_data in CROP_DATABASE.items():
            score = self._calculate_crop_suitability(crop_name, crop_data)
            if score > 0:
                # If target crop, compute age or stage adjustments for yield
                is_selected = (self.target_crop and self.target_crop.lower() == crop_name.lower())
                yield_estimate = self._estimate_yield(crop_name, crop_data, score)

                # If plantation with age specified, adjust yield for young age
                if is_selected and crop_data.get('crop_type') == 'plantation' and self.crop_age_years is not None:
                    bearing_age = crop_data.get('bearing_age_years', 4)
                    if self.crop_age_years < bearing_age:
                        yield_estimate = 0.0  # Young pre-bearing plantation

                reason = self._generate_crop_reason(crop_name, crop_data, score)

                suggestions.append({
                    'crop_name': crop_name,
                    'category': crop_data['category'],
                    'crop_type': crop_data.get('crop_type', 'seasonal'),
                    'is_selected': is_selected,
                    'suitability_score': round(score, 1),
                    'expected_yield': round(yield_estimate, 2),
                    'season': ', '.join(crop_data['season']),
                    'duration_days': crop_data['duration_days'],
                    'reason': reason,
                    'n_requirement': crop_data['n_requirement'],
                    'p_requirement': crop_data['p_requirement'],
                    'k_requirement': crop_data['k_requirement'],
                    'msp_per_quintal': crop_data.get('msp_per_quintal', 0),
                    'potential_revenue': round(
                        yield_estimate * 10 * crop_data.get('msp_per_quintal', 0), 0
                    ),
                })

        # Sort: Selected crop first (if any), then by suitability score
        suggestions.sort(
            key=lambda x: (1 if x['is_selected'] else 0, x['suitability_score']),
            reverse=True
        )
        return suggestions[:top_n]

    def _calculate_crop_suitability(self, crop_name, crop_data):
        """Calculate suitability score (0-100)."""
        score = 0
        weights = {
            'season': 25,
            'ph': 20,
            'soil_type': 15,
            'nutrients': 20,
            'weather': 15,
            'history': 5,
        }

        # 1. Season Match
        if self.season in crop_data['season'] or crop_data.get('crop_type') == 'plantation':
            score += weights['season']
        else:
            return 0  # Wrong season

        # 2. pH Suitability
        ph_min, ph_max = crop_data['ph_range']
        if ph_min <= self.soil.ph <= ph_max:
            ideal_ph = crop_data['ideal_ph']
            ph_deviation = abs(self.soil.ph - ideal_ph)
            if ph_deviation < 0.3:
                score += weights['ph']
            elif ph_deviation < 0.7:
                score += weights['ph'] * 0.8
            elif ph_deviation < 1.0:
                score += weights['ph'] * 0.6
            else:
                score += weights['ph'] * 0.4
        else:
            ph_distance = min(abs(self.soil.ph - ph_min), abs(self.soil.ph - ph_max))
            if ph_distance < 0.6:
                score += weights['ph'] * 0.25

        # 3. Soil Type Match
        if self.soil.soil_type in crop_data['soil_types']:
            score += weights['soil_type']
        else:
            score += weights['soil_type'] * 0.4

        # 4. Nutrient Availability
        n_status = self.soil.get_n_status()
        p_status = self.soil.get_p_status()
        k_status = self.soil.get_k_status()

        nutrient_score = 0
        if n_status == 'high':
            nutrient_score += 7
        elif n_status == 'medium':
            nutrient_score += 5
        else:
            nutrient_score += 3 if crop_data['n_requirement'] < 80 else 2

        if p_status == 'high':
            nutrient_score += 7
        elif p_status == 'medium':
            nutrient_score += 5
        else:
            nutrient_score += 3 if crop_data['p_requirement'] < 50 else 2

        if k_status == 'high':
            nutrient_score += 6
        elif k_status == 'medium':
            nutrient_score += 4
        else:
            nutrient_score += 3 if crop_data['k_requirement'] < 50 else 2

        score += nutrient_score

        # 5. Weather Suitability
        if self.weather:
            temp_min, temp_max = crop_data['temp_range']
            if temp_min <= self.weather.temp_avg <= temp_max:
                ideal_temp = crop_data['ideal_temp']
                temp_dev = abs(self.weather.temp_avg - ideal_temp)
                if temp_dev < 3:
                    score += weights['weather'] * 0.6
                elif temp_dev < 6:
                    score += weights['weather'] * 0.4
                else:
                    score += weights['weather'] * 0.2

                if self.weather.rainfall_mm >= crop_data['rainfall_min']:
                    score += weights['weather'] * 0.4
                elif self.weather.rainfall_mm >= crop_data['rainfall_min'] * 0.5:
                    score += weights['weather'] * 0.2
            else:
                score += weights['weather'] * 0.1
        else:
            score += weights['weather'] * 0.5

        # 6. History
        if self.history:
            recent_crops = [h.crop_grown.lower() for h in self.history[:3]]
            if crop_name.lower() in recent_crops and crop_data.get('crop_type') != 'plantation':
                score += 0  # Monoculture penalty for field crops
            else:
                score += weights['history']
        else:
            score += weights['history'] * 0.5

        return min(score, 100)

    def _estimate_yield(self, crop_name, crop_data, suitability_score):
        """Estimate expected yield."""
        base_yield = crop_data['avg_yield']
        max_yield = crop_data['max_yield']

        if suitability_score >= 85:
            yield_factor = 1.1
        elif suitability_score >= 70:
            yield_factor = 1.0
        elif suitability_score >= 55:
            yield_factor = 0.85
        elif suitability_score >= 40:
            yield_factor = 0.7
        else:
            yield_factor = 0.5

        estimated = base_yield * yield_factor

        if self.weather:
            if self.weather.rainfall_mm > 200 and crop_data['water_need'] == 'low':
                estimated *= 0.8
            elif self.weather.rainfall_mm < 20 and crop_data['water_need'] == 'high':
                estimated *= 0.7

        if self.soil.organic_carbon > 0.75:
            estimated *= 1.05
        elif self.soil.organic_carbon < 0.5:
            estimated *= 0.95

        return min(estimated, max_yield)

    def _generate_crop_reason(self, crop_name, crop_data, score):
        """Generate human-readable reason."""
        reasons = []
        if crop_data.get('crop_type') == 'plantation':
            reasons.append("Perennial plantation crop suitable for multi-year yield")
        else:
            reasons.append(f"Suitable for {self.season.capitalize()} season")

        if crop_data['ph_range'][0] <= self.soil.ph <= crop_data['ph_range'][1]:
            reasons.append(f"Soil pH {self.soil.ph} is optimal ({crop_data['ph_range'][0]}-{crop_data['ph_range'][1]})")
        else:
            reasons.append(f"Soil pH {self.soil.ph} needs correction")

        if self.soil.soil_type in crop_data['soil_types']:
            reasons.append(f"{self.soil.get_soil_type_display()} soil is favorable")

        n_status = self.soil.get_n_status()
        if n_status == 'high' and crop_data['n_requirement'] > 100:
            reasons.append("High nitrogen availability supports lush vegetative demand")
        elif n_status == 'low' and crop_data['n_requirement'] < 50:
            reasons.append("Low nutrient requirement matches soil capacity")

        return ". ".join(reasons) + "."

    # ---- FERTILIZATION CYCLE WITH AGE / GROWTH STAGE ----

    def get_fertilization_plan(self, target_crop=None, crop_age_years=None, growth_stage=None):
        """
        Generate next fertilization cycle recommendation.
        Takes into account:
        - Crop Age (in years for plantations)
        - Growth Stage (for field/seasonal crops)
        - Soil Test or Regional API base nutrient gap
        - Weather and History residual feedback
        """
        crop_name = target_crop or self.target_crop
        if not crop_name or crop_name not in CROP_DATABASE:
            suggestions = self.get_crop_suggestions(top_n=1)
            if suggestions:
                crop_name = suggestions[0]['crop_name']
            else:
                return []

        crop_data = CROP_DATABASE[crop_name]
        is_plantation = (crop_data.get('crop_type') == 'plantation')
        age_years = crop_age_years if crop_age_years is not None else self.crop_age_years
        stage = growth_stage or self.growth_stage or 'basal'

        # Base Requirements
        req_n = crop_data['n_requirement']
        req_p = crop_data['p_requirement']
        req_k = crop_data['k_requirement']

        # Age Scaling for Plantations
        age_multiplier = 1.0
        age_description = ""
        if is_plantation:
            if age_years is not None and age_years > 0:
                age_int = int(math.floor(age_years))
                scaling_dict = crop_data.get('age_scaling', {})
                max_defined_age = max(scaling_dict.keys()) if scaling_dict else 4
                effective_age = min(age_int, max_defined_age)
                age_multiplier = scaling_dict.get(effective_age, 1.0)
                age_description = f"Year {age_years:.1f} (Age dose: {int(age_multiplier*100)}% of adult requirement)"
            else:
                age_description = "Mature Bearing Plantation (Full adult dose)"

            req_n *= age_multiplier
            req_p *= age_multiplier
            req_k *= age_multiplier

        # Calculate nutrient gaps
        n_gap = self._calculate_nutrient_gap('nitrogen', req_n)
        p_gap = self._calculate_nutrient_gap('phosphorus', req_p)
        k_gap = self._calculate_nutrient_gap('potassium', req_k)

        # Weather & History Adjustments
        n_gap, p_gap, k_gap = self._weather_adjust_nutrients(n_gap, p_gap, k_gap)
        n_gap, p_gap, k_gap = self._history_adjust_nutrients(n_gap, p_gap, k_gap)

        if is_plantation:
            return self._generate_plantation_schedule(
                crop_name, crop_data, n_gap, p_gap, k_gap, age_years, age_multiplier, age_description
            )
        else:
            return self._generate_seasonal_schedule(
                crop_name, crop_data, n_gap, p_gap, k_gap, stage
            )

    def _calculate_nutrient_gap(self, nutrient, requirement):
        """Calculate nutrient gap between soil availability and crop requirement."""
        current = getattr(self.soil, nutrient, 200.0)

        if nutrient == 'nitrogen':
            available = current * 0.30
        elif nutrient == 'phosphorus':
            available = current * 0.20
        else:
            available = current * 0.50

        return max(0.0, requirement - available)

    def _weather_adjust_nutrients(self, n_gap, p_gap, k_gap):
        """
        Agro-meteorological adjustments leveraging recent past and forecast precipitation:
        - Past heavy rainfall -> Leaching replenishment (+15-25% N, +10% K)
        - Imminent heavy forecast rainfall -> Delay / split N dosing
        - Dry spell active -> Reduce dose to avoid salt stress, recommend irrigation
        """
        if not self.weather:
            return n_gap, p_gap, k_gap

        past_rain = getattr(self.weather, 'past_rainfall_7d_mm', 0.0) or 0.0
        forecast_rain = getattr(self.weather, 'forecast_rainfall_7d_mm', 0.0) or self.weather.rainfall_mm or 0.0

        # 1. Past rainfall leaching check
        if past_rain > 60:
            n_gap *= 1.20  # Nitrate leached from root zone
            k_gap *= 1.10
        elif past_rain > 120:
            n_gap *= 1.30
            k_gap *= 1.18

        # 2. Upcoming forecast rainfall check
        if forecast_rain > 80:
            # Heavy upcoming rain, adjust basal splits
            n_gap *= 1.10
        elif forecast_rain < 10 and past_rain < 10 and self.weather.humidity_percent < 50:
            # Drought/moisture stress penalty
            n_gap *= 0.88
            k_gap *= 0.88

        return n_gap, p_gap, k_gap

    def _history_adjust_nutrients(self, n_gap, p_gap, k_gap):
        """History feedback loop."""
        if not self.history:
            return n_gap, p_gap, k_gap

        recent_n, recent_p, recent_k = 0, 0, 0
        for record in self.history[:5]:
            fert_key = record.fertilizer_type
            if fert_key in FERTILIZER_DATABASE:
                fert = FERTILIZER_DATABASE[fert_key]
                qty = record.quantity_kg_per_ha
                recent_n += qty * fert['n_percent'] / 100
                recent_p += qty * fert['p_percent'] / 100
                recent_k += qty * fert['k_percent'] / 100

        residual_factor = 0.20
        n_gap = max(0.0, n_gap - recent_n * residual_factor)
        p_gap = max(0.0, p_gap - recent_p * residual_factor)
        k_gap = max(0.0, k_gap - recent_k * residual_factor)
        return n_gap, p_gap, k_gap

    def _generate_plantation_schedule(
        self, crop_name, crop_data, n_gap, p_gap, k_gap, age_years, age_multiplier, age_description
    ):
        """
        Generate schedule for Plantation / Perennial crops with age-scaled doses & palm/tree-level info.
        """
        plan = []
        today = date.today()
        plants_per_ha = crop_data.get('plants_per_ha', 1000)
        splits = crop_data.get('splits', [
            {'name': 'Pre-Monsoon Dose', 'n_pct': 0.40, 'p_pct': 0.50, 'k_pct': 0.40, 'days_offset': 15},
            {'name': 'Post-Monsoon Dose', 'n_pct': 0.60, 'p_pct': 0.50, 'k_pct': 0.60, 'days_offset': 90},
        ])

        for split in splits:
            split_name = split['name']
            offset = split.get('days_offset', 15)
            split_n = n_gap * split['n_pct']
            split_p = p_gap * split['p_pct']
            split_k = k_gap * split['k_pct']

            # DAP or SSP for Phosphorus
            if split_p > 3:
                dap_qty = split_p / (FERTILIZER_DATABASE['dap']['p_percent'] / 100)
                dap_n = dap_qty * (FERTILIZER_DATABASE['dap']['n_percent'] / 100)
                plan.append({
                    'crop_name': crop_name,
                    'crop_age_or_stage': age_description,
                    'fertilizer_type': 'dap',
                    'fertilizer_name': FERTILIZER_DATABASE['dap']['name'],
                    'quantity_kg_per_ha': round(dap_qty, 1),
                    'quantity_per_plant_g': round((dap_qty * 1000) / plants_per_ha, 1),
                    'application_stage': f"{split_name} — Phosphorus & Basal N",
                    'recommended_date': today + timedelta(days=offset),
                    'n_delivered': round(dap_n, 1),
                    'p_delivered': round(split_p, 1),
                    'k_delivered': 0,
                    'cost_per_ha': round(dap_qty * FERTILIZER_DATABASE['dap']['price_per_kg'], 0),
                    'notes': f"Dose for {age_description}. Apply in basin/ring 1-1.5m away from trunk.",
                })
                split_n = max(0, split_n - dap_n)

            # Urea for remaining Nitrogen
            if split_n > 3:
                urea_qty = split_n / (FERTILIZER_DATABASE['urea']['n_percent'] / 100)
                plan.append({
                    'crop_name': crop_name,
                    'crop_age_or_stage': age_description,
                    'fertilizer_type': 'urea',
                    'fertilizer_name': FERTILIZER_DATABASE['urea']['name'],
                    'quantity_kg_per_ha': round(urea_qty, 1),
                    'quantity_per_plant_g': round((urea_qty * 1000) / plants_per_ha, 1),
                    'application_stage': f"{split_name} — Nitrogen Dose",
                    'recommended_date': today + timedelta(days=offset),
                    'n_delivered': round(split_n, 1),
                    'p_delivered': 0,
                    'k_delivered': 0,
                    'cost_per_ha': round(urea_qty * FERTILIZER_DATABASE['urea']['price_per_kg'], 0),
                    'notes': "Incorporate into moist soil, cover with mulch.",
                })

            # MOP for Potassium
            if split_k > 3:
                mop_qty = split_k / (FERTILIZER_DATABASE['mop']['k_percent'] / 100)
                plan.append({
                    'crop_name': crop_name,
                    'crop_age_or_stage': age_description,
                    'fertilizer_type': 'mop',
                    'fertilizer_name': FERTILIZER_DATABASE['mop']['name'],
                    'quantity_kg_per_ha': round(mop_qty, 1),
                    'quantity_per_plant_g': round((mop_qty * 1000) / plants_per_ha, 1),
                    'application_stage': f"{split_name} — Potassium Dose",
                    'recommended_date': today + timedelta(days=offset),
                    'n_delivered': 0,
                    'p_delivered': 0,
                    'k_delivered': round(split_k, 1),
                    'cost_per_ha': round(mop_qty * FERTILIZER_DATABASE['mop']['price_per_kg'], 0),
                    'notes': "Critical for nut/fruit size, quality and disease resistance.",
                })

        # Organic matter / Neem cake for plantation health
        plan.append({
            'crop_name': crop_name,
            'crop_age_or_stage': age_description,
            'fertilizer_type': 'neem_cake',
            'fertilizer_name': 'Neem Cake + Organic Manure',
            'quantity_kg_per_ha': round(min(1200.0, plants_per_ha * (1.0 if (age_years or 5) < 3 else 2.0)), 1),
            'quantity_per_plant_g': round(1000 if (age_years or 5) < 3 else 2000, 0),
            'application_stage': 'Basin Ring Application (Pre-Monsoon)',
            'recommended_date': today + timedelta(days=10),
            'n_delivered': 25.0,
            'p_delivered': 5.0,
            'k_delivered': 7.0,
            'cost_per_ha': round(600 * FERTILIZER_DATABASE['neem_cake']['price_per_kg'], 0),
            'notes': "Protects against root grubs/nematodes and enhances organic carbon.",
        })

        # Micronutrient corrections
        if self.soil.boron < 0.5:
            plan.append({
                'crop_name': crop_name,
                'crop_age_or_stage': age_description,
                'fertilizer_type': 'borax',
                'fertilizer_name': 'Borax (Boron)',
                'quantity_kg_per_ha': 12.0,
                'quantity_per_plant_g': round(12000 / plants_per_ha, 1),
                'application_stage': 'Basin Application',
                'recommended_date': today + timedelta(days=20),
                'n_delivered': 0,
                'p_delivered': 0,
                'k_delivered': 0,
                'cost_per_ha': round(12.0 * FERTILIZER_DATABASE['borax']['price_per_kg'], 0),
                'notes': "Prevents crown choking, button shedding, and nut cracking.",
            })

        return plan

    def _generate_seasonal_schedule(self, crop_name, crop_data, n_gap, p_gap, k_gap, current_stage):
        """
        Generate schedule for Seasonal / Field crops tailored to current growth stage.
        """
        plan = []
        today = date.today()
        stage_ratios = crop_data.get('stage_ratios', {
            'basal': {'n': 0.33, 'p': 1.0, 'k': 0.5, 'name': 'Basal (At Sowing)'},
            'vegetative': {'n': 0.33, 'p': 0.0, 'k': 0.0, 'name': 'Vegetative / Tillering'},
            'flowering': {'n': 0.34, 'p': 0.0, 'k': 0.5, 'name': 'Flowering & Grain Filling'},
        })

        # If current stage is provided, highlight and prioritize recommendations for this stage onwards
        stage_order = ['basal', 'vegetative', 'flowering', 'fruiting', 'maturity']
        current_idx = stage_order.index(current_stage) if current_stage in stage_order else 0

        for idx, stage_key in enumerate(stage_order):
            if stage_key not in stage_ratios:
                continue

            # If stage has already passed, we skip or label as historical
            days_offset = (idx - current_idx) * 25
            if days_offset < 0:
                continue  # Skip past stages

            ratio_info = stage_ratios[stage_key]
            s_name = ratio_info['name']
            s_n = n_gap * ratio_info.get('n', 0)
            s_p = p_gap * ratio_info.get('p', 0)
            s_k = k_gap * ratio_info.get('k', 0)

            # Basal P via DAP or SSP
            if s_p > 3:
                dap_qty = s_p / (FERTILIZER_DATABASE['dap']['p_percent'] / 100)
                dap_n = dap_qty * (FERTILIZER_DATABASE['dap']['n_percent'] / 100)
                plan.append({
                    'crop_name': crop_name,
                    'crop_age_or_stage': f"Stage: {stage_key.capitalize()}",
                    'fertilizer_type': 'dap',
                    'fertilizer_name': FERTILIZER_DATABASE['dap']['name'],
                    'quantity_kg_per_ha': round(dap_qty, 1),
                    'quantity_per_plant_g': None,
                    'application_stage': f"{s_name} (Phosphorus & Basal N)",
                    'recommended_date': today + timedelta(days=max(3, days_offset)),
                    'n_delivered': round(dap_n, 1),
                    'p_delivered': round(s_p, 1),
                    'k_delivered': 0,
                    'cost_per_ha': round(dap_qty * FERTILIZER_DATABASE['dap']['price_per_kg'], 0),
                    'notes': "Apply into furrow 5cm below seed zone.",
                })
                s_n = max(0, s_n - dap_n)

            # Urea top dressings
            if s_n > 3:
                urea_qty = s_n / (FERTILIZER_DATABASE['urea']['n_percent'] / 100)
                plan.append({
                    'crop_name': crop_name,
                    'crop_age_or_stage': f"Stage: {stage_key.capitalize()}",
                    'fertilizer_type': 'urea',
                    'fertilizer_name': FERTILIZER_DATABASE['urea']['name'],
                    'quantity_kg_per_ha': round(urea_qty, 1),
                    'quantity_per_plant_g': None,
                    'application_stage': f"{s_name} — Nitrogen Split",
                    'recommended_date': today + timedelta(days=max(3, days_offset)),
                    'n_delivered': round(s_n, 1),
                    'p_delivered': 0,
                    'k_delivered': 0,
                    'cost_per_ha': round(urea_qty * FERTILIZER_DATABASE['urea']['price_per_kg'], 0),
                    'notes': "Broadcast when leaves are dry, follow with light irrigation.",
                })

            # MOP
            if s_k > 3:
                mop_qty = s_k / (FERTILIZER_DATABASE['mop']['k_percent'] / 100)
                plan.append({
                    'crop_name': crop_name,
                    'crop_age_or_stage': f"Stage: {stage_key.capitalize()}",
                    'fertilizer_type': 'mop',
                    'fertilizer_name': FERTILIZER_DATABASE['mop']['name'],
                    'quantity_kg_per_ha': round(mop_qty, 1),
                    'quantity_per_plant_g': None,
                    'application_stage': f"{s_name} — Potassium Split",
                    'recommended_date': today + timedelta(days=max(3, days_offset)),
                    'n_delivered': 0,
                    'p_delivered': 0,
                    'k_delivered': round(s_k, 1),
                    'cost_per_ha': round(mop_qty * FERTILIZER_DATABASE['mop']['price_per_kg'], 0),
                    'notes': "Enhances drought tolerance, stalk strength and grain weight.",
                })

        # Micronutrient foliar/soil correction if deficient
        if self.soil.zinc < 0.6:
            plan.append({
                'crop_name': crop_name,
                'crop_age_or_stage': f"Stage: {current_stage.capitalize()}",
                'fertilizer_type': 'zinc_sulphate',
                'fertilizer_name': 'Zinc Sulphate (Zn 21%)',
                'quantity_kg_per_ha': 25.0,
                'quantity_per_plant_g': None,
                'application_stage': 'Basal or Early Vegetative Soil Application',
                'recommended_date': today + timedelta(days=5),
                'n_delivered': 0,
                'p_delivered': 0,
                'k_delivered': 0,
                'cost_per_ha': round(25.0 * FERTILIZER_DATABASE['zinc_sulphate']['price_per_kg'], 0),
                'notes': "Prevents Khaira disease and interveinal chlorosis.",
            })

        return plan

    # ---- DERIVATIVE FORECASTS ----

    def get_derivatives(self, target_crop=None, crop_age_years=None, growth_stage=None):
        """
        Compute multi-tier derivative forecasts customized for crop type, age, and growth stage.
        """
        crop_name = target_crop or self.target_crop
        crop_data = CROP_DATABASE.get(crop_name) if crop_name else None

        if not crop_data:
            suggestions = self.get_crop_suggestions(top_n=1)
            if suggestions:
                crop_name = suggestions[0]['crop_name']
                crop_data = CROP_DATABASE[crop_name]
            else:
                return {}

        fert_plan = self.get_fertilization_plan(crop_name, crop_age_years, growth_stage)
        area = self.soil.area_hectares
        is_plantation = (crop_data.get('crop_type') == 'plantation')
        age_years = crop_age_years if crop_age_years is not None else self.crop_age_years

        # 1. Crop Yield Derivative
        score = self._calculate_crop_suitability(crop_name, crop_data)
        yield_per_ha = self._estimate_yield(crop_name, crop_data, score)

        if is_plantation and age_years is not None:
            bearing_age = crop_data.get('bearing_age_years', 4)
            if age_years < bearing_age:
                yield_per_ha = 0.0
                yield_details = f"Plantation is at Year {age_years:.1f} (Pre-bearing phase, commercial harvest starts at Year {bearing_age})."
            else:
                yield_details = f"Mature Bearing Plantation at Year {age_years:.1f}. Expected annual harvest for {area} ha."
        else:
            yield_details = f"Based on soil suitability of {score:.1f}% and {growth_stage or 'basal'} stage on {area} ha."

        total_yield = round(yield_per_ha * area, 2)
        crop_yield = {
            'type': 'crop_yield',
            'title': f"Expected Yield — {crop_name}",
            'value': total_yield,
            'unit': 'tonnes',
            'per_hectare': round(yield_per_ha, 2),
            'confidence': self._yield_confidence(score),
            'details': yield_details,
        }

        # 2. Fertilizer Demand Derivative
        total_fert_qty = sum(f['quantity_kg_per_ha'] for f in fert_plan) * area
        total_fert_cost = sum(f['cost_per_ha'] for f in fert_plan) * area
        fert_demand = {
            'type': 'fertilizer_demand',
            'title': 'Total Fertilizer Demand',
            'value': round(total_fert_qty, 1),
            'unit': 'kg',
            'cost': round(total_fert_cost, 0),
            'confidence': 88,
            'details': f"Total nutrient input for {area} ha of {crop_name} across all schedule splits.",
            'breakdown': [
                {
                    'name': f['fertilizer_name'],
                    'quantity': round(f['quantity_kg_per_ha'] * area, 1),
                    'cost': round(f['cost_per_ha'] * area, 0),
                }
                for f in fert_plan
            ],
        }

        # 3. Equipment Demand
        equipment = self._forecast_equipment(crop_name, crop_data, area, is_plantation, age_years)

        # 4. Labor Demand
        labor = self._forecast_labor(crop_name, crop_data, area, is_plantation, age_years)

        # 5. Sub-derivatives
        sub_derivatives = self._forecast_sub_derivatives(crop_name, crop_data, fert_plan, area, is_plantation, age_years)

        return {
            'crop_yield': crop_yield,
            'fertilizer_demand': fert_demand,
            'equipment_demand': equipment,
            'labor_demand': labor,
            'sub_derivatives': sub_derivatives,
        }

    def _yield_confidence(self, suitability_score):
        base = 65
        if self.weather:
            base += 10
        if self.history:
            base += 5
        return min(96, round(base + (suitability_score * 0.2)))

    def _forecast_equipment(self, crop_name, crop_data, area, is_plantation, age_years):
        items = []
        if is_plantation:
            items.append({'item': 'Tiller / Mini Tractor (Basin Intercultivation)', 'quantity': round(area * 6, 1), 'unit': 'hours'})
            items.append({'item': 'High-Pressure Power Sprayer (Canopy Care)', 'quantity': round(area * 4, 1), 'unit': 'rounds'})
            items.append({'item': 'Drip Irrigation / Fertigation Unit', 'quantity': 1, 'unit': 'system'})
            if (age_years or 5) >= crop_data.get('bearing_age_years', 4):
                items.append({'item': 'Harvesting Poles / Climbing Equipment', 'quantity': max(2, int(area * 2)), 'unit': 'sets'})
        else:
            items.append({'item': 'Tractor (Ploughing & Land Prep)', 'quantity': round(area * 8, 1), 'unit': 'hours'})
            items.append({'item': 'Rotavator / Seed Drill', 'quantity': round(area * 3, 1), 'unit': 'hours'})
            items.append({'item': 'Knapsack / Battery Sprayer', 'quantity': 3, 'unit': 'rounds'})
            if crop_data.get('category') in ['Cereal', 'Cash Crop']:
                items.append({'item': 'Combine Harvester / Thresher', 'quantity': round(area * 2, 1), 'unit': 'hours'})

        return {
            'type': 'equipment_demand',
            'title': 'Farm Machinery & Equipment Demand',
            'items': items,
            'confidence': 78,
            'details': f"Equipment allocation for {area} ha of {crop_name}.",
        }

    def _forecast_labor(self, crop_name, crop_data, area, is_plantation, age_years):
        if is_plantation:
            base_days = 90 if (age_years or 5) >= crop_data.get('bearing_age_years', 4) else 50
        else:
            cat_map = {'Cereal': 80, 'Pulse': 55, 'Oilseed': 65, 'Cash Crop': 140, 'Vegetable': 190, 'Spice': 170}
            base_days = cat_map.get(crop_data.get('category', 'Cereal'), 80)

        total_days = round(area * base_days, 0)
        daily_wage = 375  # ₹/day average
        total_cost = round(total_days * daily_wage, 0)

        activities = [
            {'activity': 'Basin Preparation / Weeding', 'days': round(total_days * 0.25, 1)},
            {'activity': 'Fertilizer & Manure Application', 'days': round(total_days * 0.20, 1)},
            {'activity': 'Irrigation & Drainage', 'days': round(total_days * 0.15, 1)},
            {'activity': 'Plant Protection Spraying', 'days': round(total_days * 0.15, 1)},
            {'activity': 'Harvesting & Post-Harvest Processing', 'days': round(total_days * 0.25, 1)},
        ]

        return {
            'type': 'labor_demand',
            'title': 'Farm Labor Demand Forecast',
            'total_labor_days': total_days,
            'total_cost': total_cost,
            'daily_wage': daily_wage,
            'activities': activities,
            'confidence': 76,
            'details': f"Forecasted {total_days:.0f} person-days for {area} ha at ₹{daily_wage}/day.",
        }

    def _forecast_sub_derivatives(self, crop_name, crop_data, fert_plan, area, is_plantation, age_years):
        sub = []
        if is_plantation:
            plants_count = crop_data.get('plants_per_ha', 1000) * area
            sub.append({'item': 'Total Trees / Palms Under Management', 'value': int(plants_count), 'unit': 'palms/trees'})
            sub.append({'item': 'Organic Mulch / Green Manure Requirement', 'value': round(area * 4000, 0), 'unit': 'kg'})
            sub.append({'item': 'Micro-Irrigation Water Requirement', 'value': round(area * 450, 0), 'unit': 'mm/year'})
            sub.append({'item': 'Bio-Pesticide & Neem Oil Requirement', 'value': round(area * 15, 1), 'unit': 'litres'})
        else:
            sub.append({'item': 'Certified Seed Requirement', 'value': round(area * 25, 1), 'unit': 'kg'})
            sub.append({'item': 'Plant Protection & Biostimulants', 'value': round(area * 3200, 0), 'unit': '₹'})
            sub.append({'item': 'Irrigation Water Requirement', 'value': round(area * 500, 0), 'unit': 'mm'})
            sub.append({'item': 'Storage / Bagging Capacity', 'value': round(crop_data['avg_yield'] * area, 1), 'unit': 'tonnes'})

        return {
            'type': 'sub_derivative',
            'title': 'Sub-derivative Cascading Demand Signals',
            'items': sub,
            'confidence': 70,
            'details': f"Supply chain, logistics and input derivatives for {area} ha.",
        }
