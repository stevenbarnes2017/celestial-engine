// API Configuration
const API_BASE = window.location.hostname.includes("127.0.0.1") || window.location.hostname.includes("localhost")
    ? "http://127.0.0.1:5000/api/auth"
    : "https://celestial-api.sundaypickems.com/api/auth";

console.log("🔍 Current hostname:", window.location.hostname);
console.log("🎯 Using API_BASE:", API_BASE);

// Global state
let currentUserData = null;
let currentPeriod = 'daily';
let currentSystem = 'western';
let currentSign = 'your-sign';

// Chinese zodiac year reference data
const CHINESE_ZODIAC_YEARS = {
    'Rat': [1924, 1936, 1948, 1960, 1972, 1984, 1996, 2008, 2020],
    'Ox': [1925, 1937, 1949, 1961, 1973, 1985, 1997, 2009, 2021],
    'Tiger': [1926, 1938, 1950, 1962, 1974, 1986, 1998, 2010, 2022],
    'Rabbit': [1927, 1939, 1951, 1963, 1975, 1987, 1999, 2011, 2023],
    'Dragon': [1928, 1940, 1952, 1964, 1976, 1988, 2000, 2012, 2024],
    'Snake': [1929, 1941, 1953, 1965, 1977, 1989, 2001, 2013, 2025],
    'Horse': [1930, 1942, 1954, 1966, 1978, 1990, 2002, 2014, 2026],
    'Goat': [1931, 1943, 1955, 1967, 1979, 1991, 2003, 2015, 2027],
    'Monkey': [1932, 1944, 1956, 1968, 1980, 1992, 2004, 2016, 2028],
    'Rooster': [1933, 1945, 1957, 1969, 1981, 1993, 2005, 2017, 2029],
    'Dog': [1934, 1946, 1958, 1970, 1982, 1994, 2006, 2018, 2030],
    'Pig': [1935, 1947, 1959, 1971, 1983, 1995, 2007, 2019, 2031]
};

// Cache structure: { period_system_sign: { content, timestamp } }
let readingsCache = {};

// ============================================================================
// AUTH FLOW
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("celestial_token");
    
    if (token) {
        showDashboard();
    } else {
        showAuthGate();
    }

    setupAuthListeners();
    setupDashboardListeners();
});

function setupAuthListeners() {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const authSubtitle = document.getElementById("auth-subtitle");
    const errorEl = document.getElementById("auth-error");
    const successEl = document.getElementById("auth-success");

    // Toggle to Registration View
    document.getElementById("go-to-register").addEventListener("click", (e) => {
        e.preventDefault();
        errorEl.classList.add("hidden");
        successEl.classList.add("hidden");
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
        document.getElementById("register-step-1").classList.remove("hidden");
        document.getElementById("register-step-2").classList.add("hidden");
        authSubtitle.textContent = "REGISTER NEW OPERATOR DATA";
    });

    // Toggle back to Login View
    document.getElementById("go-to-login").addEventListener("click", (e) => {
        e.preventDefault();
        errorEl.classList.add("hidden");
        successEl.classList.add("hidden");
        registerForm.classList.add("hidden");
        loginForm.classList.remove("hidden");
        authSubtitle.textContent = "AUTHENTICATE SYSTEM ACCESS";
    });

    // Registration Step Navigation
    document.getElementById("register-next-btn").addEventListener("click", () => {
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;

        errorEl.classList.add("hidden");

        // Validate step 1
        if (!email || !password) {
            errorEl.textContent = "Please enter both email and password.";
            errorEl.classList.remove("hidden");
            return;
        }

        if (password.length < 6) {
            errorEl.textContent = "Password must be at least 6 characters.";
            errorEl.classList.remove("hidden");
            return;
        }

        // Move to step 2
        document.getElementById("register-step-1").classList.add("hidden");
        document.getElementById("register-step-2").classList.remove("hidden");
    });

    document.getElementById("register-back-btn").addEventListener("click", () => {
        document.getElementById("register-step-2").classList.add("hidden");
        document.getElementById("register-step-1").classList.remove("hidden");
    });

    // Handle login
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;

        errorEl.classList.add("hidden");
        successEl.classList.add("hidden");

        try {
            const res = await fetch(`${API_BASE}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (res.ok && data.token) {
                localStorage.setItem("celestial_token", data.token);
                showDashboard();
            } else {
                errorEl.textContent = data.error || "Authentication handshake failed.";
                errorEl.classList.remove("hidden");
            }
        } catch (err) {
            errorEl.textContent = "Cannot connect to server gateway.";
            errorEl.classList.remove("hidden");
        }
    });

    // Handle registration with geocoding
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;
        const birthDate = document.getElementById("register-birth-date").value;
        const birthTime = document.getElementById("register-birth-time").value;
        const birthLocation = document.getElementById("register-birth-location").value;

        errorEl.classList.add("hidden");
        successEl.classList.add("hidden");

        // Validate all fields
        if (!birthDate || !birthTime || !birthLocation) {
            errorEl.textContent = "Please fill in all birth information fields.";
            errorEl.classList.remove("hidden");
            return;
        }

        // Show loading state
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = "Finding location...";
        submitBtn.disabled = true;

        try {
            // Step 1: Geocode the location to get coordinates
            submitBtn.textContent = "Geocoding location...";
            const geocodeResult = await geocodeLocation(birthLocation);
            
            if (!geocodeResult) {
                errorEl.textContent = "Could not find that location. Please try a more specific address (e.g., 'Los Angeles, CA, USA').";
                errorEl.classList.remove("hidden");
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                return;
            }

            // Step 2: Get timezone from coordinates
            submitBtn.textContent = "Detecting timezone...";
            const timezone = await getTimezoneFromCoordinates(geocodeResult.lat, geocodeResult.lng);
            
            if (!timezone) {
                errorEl.textContent = "Could not determine timezone for this location. Please try again.";
                errorEl.classList.remove("hidden");
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                return;
            }

            submitBtn.textContent = "Creating account...";

            // Register with full birth data
            const res = await fetch(`${API_BASE}/register-complete`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email,
                    password,
                    birth_date: birthDate,
                    birth_time: birthTime,
                    timezone: timezone,
                    latitude: geocodeResult.lat,
                    longitude: geocodeResult.lng,
                    location_name: geocodeResult.formatted_address
                })
            });

            const data = await res.json();

            if (res.ok && data.token) {
                successEl.textContent = "Account created! Calculating your natal chart...";
                successEl.classList.remove("hidden");
                localStorage.setItem("celestial_token", data.token);
                
                setTimeout(() => {
                    showDashboard();
                }, 1500);
            } else {
                errorEl.textContent = data.error || "Registration validation rejected.";
                errorEl.classList.remove("hidden");
            }
        } catch (err) {
            errorEl.textContent = "Cannot route data to deployment database: " + err.message;
            errorEl.classList.remove("hidden");
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });

    // Handle logout
    document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("celestial_token");
        currentUserData = null;
        readingsCache = {};
        showAuthGate();
    });
}

// Simple geocoding function using Nominatim (free, no API key required)
async function geocodeLocation(locationString) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationString)}&limit=1`,
            {
                headers: {
                    'User-Agent': 'CelestialEngine/1.0'
                }
            }
        );
        
        const data = await response.json();
        
        if (data && data.length > 0) {
            return {
                lat: parseFloat(data[0].lat),
                lng: parseFloat(data[0].lon),
                formatted_address: data[0].display_name
            };
        }
        
        return null;
    } catch (err) {
        console.error("Geocoding error:", err);
        return null;
    }
}

// Get timezone from coordinates using GeoNames API (free, requires simple registration)
async function getTimezoneFromCoordinates(lat, lng) {
    try {
        // Method 1: Using GeoNames (free but requires username)
        // For now, we'll use a public demo username - you should get your own at geonames.org
        const response = await fetch(
            `https://secure.geonames.org/timezoneJSON?lat=${lat}&lng=${lng}&username=demo`,
            {
                headers: {
                    'User-Agent': 'CelestialEngine/1.0'
                }
            }
        );
        
        const data = await response.json();
        
        if (data && data.timezoneId) {
            return data.timezoneId;
        }
        
        // Fallback: Estimate timezone from longitude
        return estimateTimezoneFromLongitude(lng);
    } catch (err) {
        console.error("Timezone detection error:", err);
        // Fallback to estimation
        return estimateTimezoneFromLongitude(lng);
    }
}

// Fallback: Rough timezone estimation from longitude
function estimateTimezoneFromLongitude(lng) {
    // This is a rough approximation - better than nothing!
    const zones = [
        { min: -180, max: -157.5, tz: 'Pacific/Honolulu' },
        { min: -157.5, max: -142.5, tz: 'America/Anchorage' },
        { min: -142.5, max: -127.5, tz: 'America/Los_Angeles' },
        { min: -127.5, max: -112.5, tz: 'America/Denver' },
        { min: -112.5, max: -97.5, tz: 'America/Chicago' },
        { min: -97.5, max: -82.5, tz: 'America/New_York' },
        { min: -82.5, max: -67.5, tz: 'America/Santiago' },
        { min: -67.5, max: -52.5, tz: 'America/Sao_Paulo' },
        { min: -52.5, max: -37.5, tz: 'Atlantic/South_Georgia' },
        { min: -37.5, max: -22.5, tz: 'Atlantic/Cape_Verde' },
        { min: -22.5, max: -7.5, tz: 'UTC' },
        { min: -7.5, max: 7.5, tz: 'Europe/London' },
        { min: 7.5, max: 22.5, tz: 'Europe/Paris' },
        { min: 22.5, max: 37.5, tz: 'Europe/Athens' },
        { min: 37.5, max: 52.5, tz: 'Asia/Dubai' },
        { min: 52.5, max: 67.5, tz: 'Asia/Karachi' },
        { min: 67.5, max: 82.5, tz: 'Asia/Kolkata' },
        { min: 82.5, max: 97.5, tz: 'Asia/Bangkok' },
        { min: 97.5, max: 112.5, tz: 'Asia/Shanghai' },
        { min: 112.5, max: 127.5, tz: 'Asia/Tokyo' },
        { min: 127.5, max: 142.5, tz: 'Australia/Sydney' },
        { min: 142.5, max: 157.5, tz: 'Pacific/Auckland' },
        { min: 157.5, max: 180, tz: 'Pacific/Fiji' }
    ];
    
    for (const zone of zones) {
        if (lng >= zone.min && lng < zone.max) {
            return zone.tz;
        }
    }
    
    return 'UTC'; // Default fallback
}

// ============================================================================
// DASHBOARD SETUP
// ============================================================================

function setupDashboardListeners() {
    // Period tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentPeriod = btn.dataset.period;
            updatePeriodTabs();
            updateUIForPeriod();
            loadCurrentReading();
        });
    });

    // System tabs
    document.querySelectorAll('.system-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentSystem = btn.dataset.system;
            updateSystemTabs();
            updateUIForSystem();
            if (currentSystem === 'overview' || currentSystem === 'sky-map') {
                loadSpecialView();
            } else {
                updateSignSelector();
                loadCurrentReading();
            }
        });
    });

    // Sign selectors
    document.getElementById('western-sign-select').addEventListener('change', (e) => {
        currentSign = e.target.value;
    });

    document.getElementById('chinese-sign-select').addEventListener('change', (e) => {
        currentSign = e.target.value;
    });

    // Year guide modal
    const showYearGuideBtn = document.getElementById('show-year-guide');
    if (showYearGuideBtn) {
        showYearGuideBtn.addEventListener('click', () => {
            console.log('📅 Opening year guide'); // Debug
            showYearGuide();
        });
    }

    const closeYearGuideBtn = document.getElementById('close-year-guide');
    if (closeYearGuideBtn) {
        closeYearGuideBtn.addEventListener('click', () => {
            console.log('❌ Closing year guide'); // Debug
            document.getElementById('year-guide-modal').classList.add('hidden');
        });
    }

    // Close modal when clicking backdrop
    const yearGuideModal = document.getElementById('year-guide-modal');
    if (yearGuideModal) {
        yearGuideModal.addEventListener('click', (e) => {
            if (e.target === yearGuideModal) {
                yearGuideModal.classList.add('hidden');
            }
        });
    }

    // Load reading button
    document.getElementById('load-reading-btn').addEventListener('click', () => {
        loadCurrentReading();
    });

    // Refresh reading button
    document.getElementById('refresh-reading-btn').addEventListener('click', () => {
        refreshCurrentReading();
    });
}

function updatePeriodTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.period === currentPeriod) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function updateSystemTabs() {
    document.querySelectorAll('.system-tab-btn').forEach(btn => {
        if (btn.dataset.system === currentSystem) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function updateSignSelector() {
    const westernSelector = document.getElementById('western-sign-selector');
    const chineseSelector = document.getElementById('chinese-sign-selector');
    const selectorTitle = document.getElementById('selector-title');

    if (currentSystem === 'western') {
        westernSelector.classList.remove('hidden');
        chineseSelector.classList.add('hidden');
        selectorTitle.textContent = 'Select Western Sign';
        currentSign = document.getElementById('western-sign-select').value;
    } else {
        westernSelector.classList.add('hidden');
        chineseSelector.classList.remove('hidden');
        selectorTitle.textContent = 'Select Chinese Sign';
        currentSign = document.getElementById('chinese-sign-select').value;
    }
}

function updateUIForSystem() {
    const leftSidebar = document.querySelector('.lg\\:col-span-1');
    const periodTabs = document.querySelector('.tab-btn').parentElement.parentElement;
    
    if (currentSystem === 'overview' || currentSystem === 'sky-map') {
        // Hide period tabs and sidebar for special views
        periodTabs.classList.add('hidden');
        leftSidebar.classList.add('hidden');
    } else {
        // Show period tabs and sidebar for normal views
        periodTabs.classList.remove('hidden');
        leftSidebar.classList.remove('hidden');
    }
}

function showYearGuide() {
    const modal = document.getElementById('year-guide-modal');
    const content = document.getElementById('year-guide-content');
    
    let html = '';
    
    for (const [animal, years] of Object.entries(CHINESE_ZODIAC_YEARS)) {
        const emoji = getChineseSignEmoji(animal);
        const recentYears = years.slice(-6).join(', '); // Last 6 years
        
        html += `
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition">
                <div class="flex items-center space-x-2 mb-2">
                    <span class="text-2xl">${emoji}</span>
                    <span class="font-bold text-zinc-200">${animal}</span>
                </div>
                <p class="text-xs text-zinc-500 mb-1">Recent years:</p>
                <p class="text-sm text-zinc-300 font-mono">${recentYears}</p>
            </div>
        `;
    }
    
    content.innerHTML = html;
    modal.classList.remove('hidden');
}
    
    

function updateUIForPeriod() {
    const transitPanel = document.getElementById('transit-panel');
    const readingTitle = document.getElementById('reading-title');
    
    // Show transits only for daily
    if (currentPeriod === 'daily') {
        transitPanel.classList.remove('hidden');
    } else {
        transitPanel.classList.add('hidden');
    }

    // Update title
    const periodTitles = {
        'daily': 'Daily Analysis',
        'weekly': 'Weekly Forecast',
        'monthly': 'Monthly Overview',
        'yearly': 'Yearly Predictions'
    };
    
    readingTitle.textContent = `Personalized ${periodTitles[currentPeriod]}`;
}

// ============================================================================
// UI DISPLAY FUNCTIONS
// ============================================================================

function showAuthGate() {
    document.getElementById("auth-gate").classList.remove("hidden");
    document.getElementById("dashboard").classList.add("hidden");
}

function showDashboard() {
    document.getElementById("auth-gate").classList.add("hidden");
    document.getElementById("dashboard").classList.remove("hidden");
    fetchUserProfile();
}

// ============================================================================
// DATA FETCHING
// ============================================================================

async function fetchUserProfile() {
    const token = localStorage.getItem("celestial_token");
    
    try {
        const res = await fetch(`${API_BASE}/current-chart`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (res.status === 401) {
            localStorage.removeItem("celestial_token");
            showAuthGate();
            return;
        }

        const data = await res.json();
        currentUserData = data;

        // Display user's signs in header
        displayUserSigns(data);
        
        // Load default reading (daily, western, user's sign)
        loadCurrentReading();

    } catch (err) {
        console.error("Failed to fetch user profile:", err);
    }
}

function displayUserSigns(userData) {
    const westernSignEl = document.getElementById('user-western-sign');
    const chineseSignEl = document.getElementById('user-chinese-sign');

    if (userData.western_chart && userData.western_chart.planets && userData.western_chart.planets.Sun) {
        const sunSign = userData.western_chart.planets.Sun.zodiac_sign;
        westernSignEl.textContent = `☉ ${sunSign}`;
    }

    if (userData.eastern_bazi && userData.eastern_bazi.Year_Pillar) {
        const chineseSign = userData.eastern_bazi.Year_Pillar.Branch;
        chineseSignEl.textContent = `${getChineseSignEmoji(chineseSign)} ${chineseSign}`;
    }
}

function getChineseSignEmoji(sign) {
    const emojiMap = {
        'Rat': '🐀', 'Ox': '🐂', 'Tiger': '🐅', 'Rabbit': '🐇',
        'Dragon': '🐉', 'Snake': '🐍', 'Horse': '🐴', 'Goat': '🐐',
        'Monkey': '🐒', 'Rooster': '🐓', 'Dog': '🐕', 'Pig': '🐖'
    };
    return emojiMap[sign] || '🌟';
}

// ============================================================================
// SPECIAL VIEWS (Overview & Sky Map)
// ============================================================================

async function loadSpecialView() {
    const token = localStorage.getItem("celestial_token");
    const horoscopeContent = document.getElementById("horoscope-content");
    const readingTitle = document.getElementById("reading-title");
    const refreshBtn = document.getElementById("refresh-reading-btn");
    
    if (currentSystem === 'overview') {
        readingTitle.textContent = "Your Complete Astrological Profile";
        refreshBtn.classList.add('hidden');
        
        horoscopeContent.innerHTML = `
            <div class="flex items-center justify-center p-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500 mr-3"></div>
                <span class="text-zinc-400">Loading your natal chart profile...</span>
            </div>
        `;
        
        try {
            const res = await fetch(`${API_BASE}/current-chart`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
            
            if (res.status === 401) {
                localStorage.removeItem("celestial_token");
                showAuthGate();
                return;
            }
            
            const data = await res.json();
            displayProfileOverview(data);
            
        } catch (err) {
            horoscopeContent.innerHTML = `
                <p class="text-red-400 text-sm">Error loading profile. Please try again.</p>
            `;
        }
    } else if (currentSystem === 'sky-map') {
        readingTitle.textContent = "Today's Celestial Snapshot";
        refreshBtn.classList.remove('hidden');
        
        horoscopeContent.innerHTML = `
            <div class="flex items-center justify-center p-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500 mr-3"></div>
                <span class="text-zinc-400">Calculating current planetary positions...</span>
            </div>
        `;
        
        try {
            const res = await fetch(`${API_BASE}/current-sky`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
            
            if (res.status === 401) {
                localStorage.removeItem("celestial_token");
                showAuthGate();
                return;
            }
            
            const data = await res.json();
            displaySkyMap(data);
            
        } catch (err) {
            horoscopeContent.innerHTML = `
                <p class="text-red-400 text-sm">Error loading sky map. Please try again.</p>
            `;
        }
    }
}

function displayProfileOverview(userData) {
    const horoscopeContent = document.getElementById("horoscope-content");
    const currentSignDisplay = document.getElementById("current-sign-display");
    
    currentSignDisplay.textContent = "Your Complete Profile";
    
    let html = '';
    
    // Check if user has birth data
    if (!userData.birth_telemetry || !userData.western_chart.planets.Sun) {
        html = `
            <div class="text-center py-12">
                <div class="text-6xl mb-4">🌟</div>
                <h3 class="text-xl font-bold text-zinc-200 mb-2">Complete Your Celestial Profile</h3>
                <p class="text-zinc-400 mb-6">Add your birth information to unlock your personalized natal chart analysis</p>
                <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-6 max-w-md mx-auto text-left space-y-3">
                    <p class="text-xs text-zinc-500 uppercase tracking-wide font-bold">We'll need:</p>
                    <ul class="text-sm text-zinc-300 space-y-2">
                        <li>📅 Your birth date</li>
                        <li>⏰ Your birth time (as accurate as possible)</li>
                        <li>📍 Your birth location</li>
                    </ul>
                </div>
                <p class="text-xs text-zinc-600 mt-6">Feature coming soon - Birth data collection form</p>
            </div>
        `;
    } else {
        // Display comprehensive profile
        const planets = userData.western_chart.planets;
        const houses = userData.western_chart.houses;
        const angles = userData.western_chart.angles;
        const aspects = userData.western_chart.aspects;
        const bazi = userData.eastern_bazi;
        
        html = `
            <div class="space-y-6">
                <!-- Western Chart Section -->
                <div class="border-b border-zinc-800 pb-6">
                    <h3 class="text-sm font-bold uppercase tracking-wider text-violet-400 mb-4">🌟 Western Natal Chart</h3>
                    
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                        ${Object.entries(planets).map(([planet, data]) => `
                            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3">
                                <div class="text-xs text-zinc-500 uppercase">${planet}</div>
                                <div class="text-sm font-semibold text-zinc-200">${data.zodiac_sign}</div>
                                <div class="text-xs font-mono text-zinc-600">${data.absolute_degree.toFixed(2)}°</div>
                            </div>
                        `).join('')}
                    </div>
                    
                    ${angles ? `
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="bg-violet-950/20 border border-violet-900/50 rounded-lg p-3">
                            <div class="text-xs text-violet-400 uppercase font-bold">Ascendant (Rising)</div>
                            <div class="text-base font-semibold text-zinc-100">${angles.Ascendant.zodiac_sign}</div>
                            <div class="text-xs font-mono text-zinc-500">${angles.Ascendant.absolute_degree.toFixed(2)}°</div>
                        </div>
                        <div class="bg-violet-950/20 border border-violet-900/50 rounded-lg p-3">
                            <div class="text-xs text-violet-400 uppercase font-bold">Midheaven (MC)</div>
                            <div class="text-base font-semibold text-zinc-100">${angles.Midheaven.zodiac_sign}</div>
                            <div class="text-xs font-mono text-zinc-500">${angles.Midheaven.absolute_degree.toFixed(2)}°</div>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${aspects && aspects.length > 0 ? `
                    <div>
                        <h4 class="text-xs font-bold text-zinc-400 uppercase mb-2">Major Aspects</h4>
                        <div class="space-y-2">
                            ${aspects.slice(0, 6).map(asp => `
                                <div class="bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs">
                                    <span class="text-zinc-300">${asp.planet_a}</span>
                                    <span class="text-${asp.aspect === 'Square' || asp.aspect === 'Opposition' ? 'red' : 'emerald'}-400 font-semibold mx-2">${asp.aspect}</span>
                                    <span class="text-zinc-300">${asp.planet_b}</span>
                                    <span class="text-zinc-600 ml-2">(${asp.orb_variance.toFixed(1)}° orb)</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
                
                <!-- Eastern BaZi Section -->
                ${bazi && bazi.Year_Pillar ? `
                <div class="border-b border-zinc-800 pb-6">
                    <h3 class="text-sm font-bold uppercase tracking-wider text-amber-400 mb-4">🐉 Eastern Four Pillars (BaZi)</h3>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                        ${['Year_Pillar', 'Month_Pillar', 'Day_Pillar', 'Hour_Pillar'].map(pillar => `
                            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3">
                                <div class="text-xs text-zinc-500 uppercase mb-1">${pillar.replace('_', ' ')}</div>
                                <div class="text-sm font-semibold text-amber-300">${bazi[pillar].Stem}</div>
                                <div class="text-sm text-zinc-300">${bazi[pillar].Branch}</div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="mt-4 bg-amber-950/20 border border-amber-900/50 rounded-lg p-4">
                        <div class="text-xs text-amber-400 uppercase font-bold mb-1">Day Master</div>
                        <div class="text-base font-semibold text-zinc-100">${bazi.Day_Pillar.Stem}</div>
                        <div class="text-xs text-zinc-400 mt-1">Your core elemental identity in Chinese astrology</div>
                    </div>
                </div>
                ` : ''}
                
                <!-- Interpretation -->
                ${userData.authentic_horoscope ? `
                <div>
                    <h3 class="text-sm font-bold uppercase tracking-wider text-zinc-400 mb-4">💫 Integrated Interpretation</h3>
                    <div class="prose prose-invert max-w-none text-zinc-300 text-sm leading-relaxed">
                        ${formatMarkdown(userData.authentic_horoscope)}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    horoscopeContent.innerHTML = html;
    horoscopeContent.classList.add('fade-in');
}

function displaySkyMap(skyData) {
    const horoscopeContent = document.getElementById("horoscope-content");
    const currentSignDisplay = document.getElementById("current-sign-display");
    const dateLabel = document.getElementById("forecast-date");
    
    currentSignDisplay.textContent = "Current Sky";
    dateLabel.textContent = skyData.current_date || new Date().toISOString().split('T')[0];
    
    const planets = skyData.current_positions || {};
    const interpretation = skyData.interpretation || '';
    
    let html = `
        <div class="space-y-6">
            <!-- Current Planetary Positions -->
            <div class="border-b border-zinc-800 pb-6">
                <h3 class="text-sm font-bold uppercase tracking-wider text-violet-400 mb-4">🌌 Current Planetary Positions</h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                    ${Object.entries(planets).map(([planet, data]) => `
                        <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3 hover:border-zinc-700 transition">
                            <div class="flex justify-between items-start mb-2">
                                <span class="text-xs text-zinc-500 uppercase">${planet}</span>
                                <span class="text-xs font-mono text-zinc-600">${data.absolute_degree?.toFixed(2)}°</span>
                            </div>
                            <div class="text-base font-semibold text-zinc-200">${data.zodiac_sign}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <!-- Sky Interpretation -->
            ${interpretation ? `
            <div>
                <h3 class="text-sm font-bold uppercase tracking-wider text-zinc-400 mb-4">✨ Today's Cosmic Weather</h3>
                <div class="prose prose-invert max-w-none text-zinc-300 text-sm leading-relaxed">
                    ${formatMarkdown(interpretation)}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    horoscopeContent.innerHTML = html;
    horoscopeContent.classList.add('fade-in');
}

// ============================================================================
// READING LOADING WITH CACHING
// ============================================================================

function getCacheKey() {
    return `${currentPeriod}_${currentSystem}_${currentSign}`;
}

function isCacheValid(cacheEntry) {
    if (!cacheEntry) return false;
    
    const now = new Date();
    const cached = new Date(cacheEntry.timestamp);
    
    // Determine cache validity based on period
    switch (currentPeriod) {
        case 'daily':
            // Valid if same calendar day
            return cached.toDateString() === now.toDateString();
        case 'weekly':
            // Valid if same week
            const weekStart = new Date(now);
            weekStart.setDate(now.getDate() - now.getDay());
            return cached >= weekStart;
        case 'monthly':
            // Valid if same month
            return cached.getMonth() === now.getMonth() && 
                   cached.getFullYear() === now.getFullYear();
        case 'yearly':
            // Valid if same year
            return cached.getFullYear() === now.getFullYear();
        default:
            return false;
    }
}

async function loadCurrentReading() {
    const cacheKey = getCacheKey();
    const cached = readingsCache[cacheKey];

    // Check if we have valid cached data
    if (isCacheValid(cached)) {
        displayReading(cached.content, true, cached.timestamp);
        return;
    }

    // Fetch new reading
    await fetchNewReading();
}

async function refreshCurrentReading() {
    // Force fetch new reading, bypassing cache
    const confirmRefresh = confirm(
        "This will generate a new reading. Your current reading will be replaced. Continue?"
    );
    
    if (confirmRefresh) {
        await fetchNewReading(true);
    }
}

async function fetchNewReading(forceRefresh = false) {
    const token = localStorage.getItem("celestial_token");
    const horoscopeContent = document.getElementById("horoscope-content");
    
    // Show loading state
    horoscopeContent.innerHTML = `
        <div class="flex items-center justify-center p-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500 mr-3"></div>
            <span class="text-zinc-400">Generating ${currentPeriod} reading for ${currentSign === 'your-sign' ? 'your sign' : currentSign}...</span>
        </div>
    `;

    try {
        // Build request parameters
        const params = new URLSearchParams({
            period: currentPeriod,
            system: currentSystem,
            sign: currentSign,
            force_refresh: forceRefresh
        });

        const res = await fetch(`${API_BASE}/horoscope?${params}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (res.status === 401) {
            localStorage.removeItem("celestial_token");
            showAuthGate();
            return;
        }

        const data = await res.json();

        // Handle different response structures
        let readingContent = '';
        let transitData = null;
        
        if (currentPeriod === 'daily' && data.daily_horoscope) {
            readingContent = data.daily_horoscope;
            transitData = data.active_geometric_transits;
            updateDate(data.date_today);
        } else if (data.horoscope) {
            readingContent = data.horoscope;
        } else if (data.reading) {
            readingContent = data.reading;
        } else {
            readingContent = "Reading data not available.";
        }

        // Cache the reading
        const cacheKey = getCacheKey();
        readingsCache[cacheKey] = {
            content: readingContent,
            timestamp: new Date().toISOString(),
            transits: transitData
        };

        // Display the reading
        displayReading(readingContent, false, readingsCache[cacheKey].timestamp);
        
        // Display transits if daily
        if (currentPeriod === 'daily' && transitData) {
            displayTransits(transitData);
        }

    } catch (err) {
        horoscopeContent.innerHTML = `
            <p class="text-red-400 text-sm">Error loading reading. Please try again.</p>
            <p class="text-zinc-600 text-xs mt-2">${err.message}</p>
        `;
    }
}

function displayReading(content, isCached, timestamp) {
    const horoscopeContent = document.getElementById("horoscope-content");
    const cacheIndicator = document.getElementById("cache-indicator");
    const cacheTime = document.getElementById("cache-time");
    const currentSignDisplay = document.getElementById("current-sign-display");

    // Format the content
    horoscopeContent.innerHTML = formatMarkdown(content);
    horoscopeContent.classList.add('fade-in');

    // Update sign display
    if (currentSign === 'your-sign') {
        if (currentSystem === 'western' && currentUserData?.western_chart?.planets?.Sun) {
            currentSignDisplay.textContent = `Your Sign (${currentUserData.western_chart.planets.Sun.zodiac_sign})`;
        } else if (currentSystem === 'chinese' && currentUserData?.eastern_bazi?.Year_Pillar) {
            currentSignDisplay.textContent = `Your Sign (${currentUserData.eastern_bazi.Year_Pillar.Branch})`;
        } else {
            currentSignDisplay.textContent = 'Your Sign';
        }
    } else {
        currentSignDisplay.textContent = currentSign;
    }

    // Show cache indicator
    if (isCached && timestamp) {
        cacheIndicator.classList.remove('hidden');
        const date = new Date(timestamp);
        cacheTime.textContent = date.toLocaleString();
    } else {
        cacheIndicator.classList.add('hidden');
    }
}

function displayTransits(transits) {
    const transitList = document.getElementById("transit-list");
    
    transitList.innerHTML = "";
    
    if (transits && transits.length > 0) {
        transits.forEach(t => {
            const card = document.createElement("div");
            card.className = "transit-card p-3 rounded-lg text-xs space-y-1";
            
            const badgeColor = t.aspect === "Square" || t.aspect === "Opposition" 
                ? "text-red-400 bg-red-950/30 border-red-900/50" 
                : "text-emerald-400 bg-emerald-950/30 border-emerald-900/50";
            
            card.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="font-semibold text-zinc-300">Moving ${t.transit_planet}</span>
                    <span class="px-2 py-0.5 border rounded-full text-[10px] uppercase font-mono ${badgeColor}">${t.aspect}</span>
                </div>
                <div class="text-zinc-500 font-medium">Hitting Natal <span class="text-zinc-300">${t.natal_planet}</span></div>
                <div class="text-[10px] text-zinc-600 font-mono">Orb: ${t.orb_variance}°</div>
            `;
            transitList.appendChild(card);
        });
    } else {
        transitList.innerHTML = `
            <div class="text-center py-8">
                <p class="text-zinc-400 text-sm mb-2">🌙 Quiet Skies Today</p>
                <p class="text-zinc-600 text-xs">No major planetary aspects detected</p>
            </div>
        `;
    }
}

function updateDate(dateStr) {
    const dateLabel = document.getElementById("forecast-date");
    if (dateStr) {
        dateLabel.textContent = dateStr;
    } else {
        dateLabel.textContent = new Date().toISOString().split('T')[0];
    }
}

// ============================================================================
// MARKDOWN FORMATTING
// ============================================================================

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-zinc-100 font-bold block text-base mt-4 mb-1">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="text-violet-300">$1</em>')
        .replace(/\n\n/g, '</p><p class="mt-3">')
        .replace(/\n/g, '<br>');
}