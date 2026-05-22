// API Configuration
const API_BASE = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:5000/api/auth"
    : "https://celestial-engine-arba.onrender.com/api/auth";

// Global state
let currentUserData = null;
let currentPeriod = 'daily';
let currentSystem = 'western';
let currentSign = 'your-sign';

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

    // Handle registration
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;

        errorEl.classList.add("hidden");
        successEl.classList.add("hidden");

        try {
            const res = await fetch(`${API_BASE}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (res.ok) {
                successEl.textContent = "Profile registered! You can now log in.";
                successEl.classList.remove("hidden");
                registerForm.reset();
                setTimeout(() => {
                    document.getElementById("go-to-login").click();
                }, 1500);
            } else {
                errorEl.textContent = data.error || "Registration validation rejected.";
                errorEl.classList.remove("hidden");
            }
        } catch (err) {
            errorEl.textContent = "Cannot route data to deployment database.";
            errorEl.classList.remove("hidden");
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
            updateSignSelector();
            loadCurrentReading();
        });
    });

    // Sign selectors
    document.getElementById('western-sign-select').addEventListener('change', (e) => {
        currentSign = e.target.value;
    });

    document.getElementById('chinese-sign-select').addEventListener('change', (e) => {
        currentSign = e.target.value;
    });

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