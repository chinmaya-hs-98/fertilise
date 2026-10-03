/**
 * Soil Engine — Frontend JavaScript & Interactive Agronomic Intelligence
 * Handles Geo-API auto-fill, dynamic crop age/stage controls, micro-animations, and score ring rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ---- Animate elements on scroll ----
    const observerOptions = {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px',
    };

    const animateOnScroll = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                animateOnScroll.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe cards and sections
    document.querySelectorAll(
        '.stat-card, .step-card, .crop-card, .derivative-card, .result-card, .form-section, .geo-api-card, .simulator-card'
    ).forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(16px)';
        el.style.transition = 'opacity 0.45s cubic-bezier(0.16, 1, 0.3, 1), transform 0.45s cubic-bezier(0.16, 1, 0.3, 1)';
        animateOnScroll.observe(el);
    });

    // CSS class for animation
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);

    // ---- Animate stat counters ----
    document.querySelectorAll('.stat-value').forEach(counter => {
        const target = parseInt(counter.textContent);
        if (isNaN(target)) return;

        counter.textContent = '0';
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(counter, target);
                    observer.unobserve(entry.target);
                }
            });
        });
        observer.observe(counter);
    });

    function animateCounter(element, target) {
        const duration = 900;
        const start = performance.now();

        function update(current) {
            const elapsed = current - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.round(eased * target);
            element.textContent = value;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = target;
            }
        }

        requestAnimationFrame(update);
    }

    // ---- Score ring color coding ----
    document.querySelectorAll('.score-ring').forEach(ring => {
        const score = parseFloat(ring.dataset.score);
        const fill = ring.querySelector('.score-fill');
        const text = ring.querySelector('.score-text');

        if (!fill) return;

        if (score >= 80) {
            fill.style.stroke = '#22c55e';
            if (text) text.style.color = '#15803d';
        } else if (score >= 60) {
            fill.style.stroke = '#eab308';
            if (text) text.style.color = '#ca8a04';
        } else if (score >= 40) {
            fill.style.stroke = '#f97316';
            if (text) text.style.color = '#ea580c';
        } else {
            fill.style.stroke = '#ef4444';
            if (text) text.style.color = '#dc2626';
        }
    });

    // =========================================================================
    // GEO-SOIL API AUTO-FETCH & REGIONAL FALLBACK
    // =========================================================================
    const geoInput = document.getElementById('geo-search-input');
    const geoBtn = document.getElementById('btn-fetch-geo');
    const geoStatusBox = document.getElementById('geo-status-box');
    const geoStatusTitle = document.getElementById('geo-status-title');
    const geoStatusDesc = document.getElementById('geo-status-desc');

    if (geoBtn && geoInput) {
        geoBtn.addEventListener('click', () => {
            const query = geoInput.value.trim();
            if (!query) {
                geoInput.focus();
                return;
            }
            performGeoFetch(query);
        });

        geoInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                geoBtn.click();
            }
        });

        // Quick Tags
        document.querySelectorAll('.geo-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const place = tag.getAttribute('data-place');
                geoInput.value = place;
                performGeoFetch(place);
            });
        });
    }

    async function performGeoFetch(placeQuery) {
        if (!geoStatusBox) return;

        geoStatusBox.style.display = 'flex';
        geoStatusBox.className = 'geo-status-box loading';
        geoStatusTitle.textContent = 'Querying Free Geo-Soil API & ICAR Database...';
        geoStatusDesc.textContent = `Resolving soil profile for "${placeQuery}" via ISRIC SoilGrids 2.0 & Taluk Health Cards...`;

        try {
            const url = `/api/geo-soil/?location=${encodeURIComponent(placeQuery)}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('API server returned error status');

            const data = await response.json();

            // Populate form fields
            setFieldValue('id_location_input', data.location_matched || placeQuery);
            setFieldValue('id_nitrogen', data.nitrogen);
            setFieldValue('id_phosphorus', data.phosphorus);
            setFieldValue('id_potassium', data.potassium);
            setFieldValue('id_ph', data.ph);
            setFieldValue('id_organic_carbon', data.organic_carbon);
            setFieldValue('id_electrical_conductivity', data.electrical_conductivity || 0.35);
            setFieldValue('id_sulphur', data.sulphur || 12.0);
            setFieldValue('id_zinc', data.zinc || 0.45);
            setFieldValue('id_iron', data.iron || 6.5);
            setFieldValue('id_manganese', data.manganese || 3.5);
            setFieldValue('id_copper', data.copper || 0.35);
            setFieldValue('id_boron', data.boron || 0.40);

            // Select matching soil type and texture
            setSelectValue('id_soil_type', data.soil_type);
            setSelectValue('id_texture', data.texture);
            setSelectValue('id_data_source', 'regional_api');
            setFieldValue('id_source_details', `${data.source} (Confidence: ${data.confidence}%)`);

            // Flash updated inputs with smooth green highlight
            triggerInputGlow();

            // Update status box
            geoStatusBox.className = 'geo-status-box success';
            geoStatusTitle.textContent = `✓ Soil Data Loaded for ${data.location_matched || placeQuery}`;
            geoStatusDesc.textContent = `Source: ${data.source} | Confidence: ${data.confidence}% | N-P-K: ${data.nitrogen}-${data.phosphorus}-${data.potassium} kg/ha, pH: ${data.ph}`;

        } catch (err) {
            console.error('Geo fetch error:', err);
            geoStatusBox.className = 'geo-status-box error';
            geoStatusTitle.textContent = 'Lookup Notice: Falling back to National Agro-Ecological Baseline';
            geoStatusDesc.textContent = 'Using representative ICAR regional standard data for this agro-climatic zone.';
        }
    }

    function setFieldValue(id, val) {
        const el = document.getElementById(id);
        if (el && val !== undefined && val !== null) {
            el.value = val;
            // Trigger change event to refresh color coding
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    function setSelectValue(id, val) {
        const el = document.getElementById(id);
        if (el && val) {
            for (let i = 0; i < el.options.length; i++) {
                if (el.options[i].value.toLowerCase() === val.toLowerCase()) {
                    el.selectedIndex = i;
                    break;
                }
            }
        }
    }

    function triggerInputGlow() {
        document.querySelectorAll('#id_nitrogen, #id_phosphorus, #id_potassium, #id_ph, #id_organic_carbon').forEach(inp => {
            inp.classList.add('pulse-highlight');
            setTimeout(() => inp.classList.remove('pulse-highlight'), 1600);
        });
    }

    // =========================================================================
    // DYNAMIC CROP SELECTION & PLANTATION AGE / GROWTH STAGE TOGGLE
    // =========================================================================
    const cropSelect = document.getElementById('id_selected_crop');
    const plantationAgeGroup = document.getElementById('group-plantation-age');
    const growthStageGroup = document.getElementById('group-growth-stage');
    const ageInput = document.getElementById('id_crop_age_years');
    const ageAnnotation = document.getElementById('age-annotation');

    // Plantations list
    const plantationKeywords = ['arecanut', 'coconut', 'coffee', 'rubber', 'mango', 'pepper', 'banana', 'cashew', 'citrus', 'tea', 'cardamom'];

    function isPlantationCrop(cropName) {
        if (!cropName) return false;
        const lower = cropName.toLowerCase();
        return plantationKeywords.some(k => lower.includes(k));
    }

    function updateCropControls() {
        if (!cropSelect) return;
        const selectedText = cropSelect.value;
        const isPlantation = isPlantationCrop(selectedText);

        if (plantationAgeGroup) {
            plantationAgeGroup.style.display = isPlantation ? 'block' : 'none';
        }
        if (growthStageGroup) {
            growthStageGroup.style.display = isPlantation ? 'none' : 'block';
        }

        updateAgeAnnotation();
    }

    function updateAgeAnnotation() {
        if (!ageInput || !ageAnnotation) return;
        const val = parseFloat(ageInput.value);
        if (isNaN(val) || val <= 0) {
            ageAnnotation.textContent = 'Enter plantation age in years';
            return;
        }

        if (val < 1.5) {
            ageAnnotation.textContent = 'Seedling / 1st Year: ~33% of adult dose (Establishment phase)';
        } else if (val < 2.5) {
            ageAnnotation.textContent = '2nd Year Young Palm/Tree: ~66% of adult dose (Vegetative development)';
        } else if (val < 3.5) {
            ageAnnotation.textContent = '3rd Year Developing: ~85% of adult dose (Pre-bearing phase)';
        } else {
            ageAnnotation.textContent = '4+ Years: 100% Full adult commercial bearing dose';
        }
    }

    if (cropSelect) {
        cropSelect.addEventListener('change', updateCropControls);
        updateCropControls();
    }

    if (ageInput) {
        ageInput.addEventListener('input', updateAgeAnnotation);
        updateAgeAnnotation();
    }

    // =========================================================================
    // NUTRIENT VALUE DYNAMIC COLOR CODING
    // =========================================================================
    const nitrogenInput = document.getElementById('id_nitrogen');
    const phosphorusInput = document.getElementById('id_phosphorus');
    const potassiumInput = document.getElementById('id_potassium');
    const phInput = document.getElementById('id_ph');

    function colorCodeInput(input, ranges) {
        if (!input) return;
        const handler = () => {
            const val = parseFloat(input.value);
            if (isNaN(val)) {
                input.style.borderColor = '';
                input.style.backgroundColor = '';
                return;
            }
            if (val < ranges[0]) {
                input.style.borderColor = '#ef4444';
                input.style.backgroundColor = '#fef2f2';
            } else if (val <= ranges[1]) {
                input.style.borderColor = '#eab308';
                input.style.backgroundColor = '#fefce8';
            } else {
                input.style.borderColor = '#22c55e';
                input.style.backgroundColor = '#f0fdf4';
            }
        };
        input.addEventListener('input', handler);
        handler(); // run initially
    }

    colorCodeInput(nitrogenInput, [280, 560]);
    colorCodeInput(phosphorusInput, [10, 24.6]);
    colorCodeInput(potassiumInput, [108, 280]);

    if (phInput) {
        const phHandler = () => {
            const val = parseFloat(phInput.value);
            if (isNaN(val)) {
                phInput.style.borderColor = '';
                phInput.style.backgroundColor = '';
                return;
            }
            if (val < 6.5) {
                phInput.style.borderColor = '#eab308';
                phInput.style.backgroundColor = '#fefce8';
            } else if (val <= 7.5) {
                phInput.style.borderColor = '#22c55e';
                phInput.style.backgroundColor = '#f0fdf4';
            } else {
                phInput.style.borderColor = '#ef4444';
                phInput.style.backgroundColor = '#fee2e2';
            }
        };
        phInput.addEventListener('input', phHandler);
        phHandler();
    }

    // Flow diagram animation on dashboard
    const flowNodes = document.querySelectorAll('.flow-node');
    if (flowNodes.length > 0) {
        let delay = 0;
        flowNodes.forEach(node => {
            node.style.opacity = '0';
            node.style.transform = 'scale(0.85)';
            setTimeout(() => {
                node.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
                node.style.opacity = '1';
                node.style.transform = 'scale(1)';
            }, delay);
            delay += 120;
        });
    }

    console.log('🌱 Soil Engine UI & Geo Intelligence Initialized');
});
