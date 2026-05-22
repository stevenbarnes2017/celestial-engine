// Automatically toggles between your local dev environment and your live production URL
const API_BASE = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:5000/api/auth"
    : "https://celestial-engine-arba.onrender.com/api/auth";

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("celestial_token");
    
    if (token) {
        showDashboard();
    } else {
        showAuthGate();
    }

    // Form Navigation Elements
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

    // Handle authentication form submission
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

    
    // Handle registration form submission with automated geocoding telemetry
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;
        const birthDate = document.getElementById("register-birth-date").value;
        const birthTime = document.getElementById("register-birth-time").value;
        const birthPlace = document.getElementById("register-birth-place").value;

        errorEl.classList.add("hidden");
        successEl.classList.add("hidden");
        
        // Visual indicator that telemetry is calculating
        const submitBtn = registerForm.querySelector("button[type='submit']");
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = "CALCULATING TELEMETRY GRIDS...";
        submitBtn.disabled = true;

        try {
            // 1. Fetch Latitude & Longitude from OpenStreetMap Nominatim API
            const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(birthPlace)}&limit=1`);
            const geoData = await geoRes.json();

            if (!geoData || geoData.length === 0) {
                throw new Error("Could not resolve geospatial metrics for birth place location.");
            }

            const lat = parseFloat(geoData[0].lat);
            const lon = parseFloat(geoData[0].lon);

            // 2. Infer timezone offset mapping based on coordinates
            // Using a free lookup or evaluating the native browser region as a fallback
            let resolvedTimezone = "America/New_York"; // Default pipeline fallback
            try {
                const tzRes = await fetch(`https://www.timeapi.io/api/TimeZone/coordinate?latitude=${lat}&longitude=${lon}`);
                if (tzRes.ok) {
                    const tzData = await tzRes.json();
                    resolvedTimezone = tzData.timeZone || resolvedTimezone;
                }
            } catch (tzErr) {
                // Fail-safe: Fallback to evaluating regional location matrix if third-party time API times out
                resolvedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            }

            // 3. Ensure time format has seconds suffix if backend database expects HH:MM:SS
            const formattedTime = birthTime.length === 5 ? `${birthTime}:00` : birthTime;

            // 4. Route final compiled data payload to Render backend API
            const res = await fetch(`${API_BASE}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    email: email, 
                    password: password,
                    birth_date: birthDate,
                    birth_time: formattedTime,
                    birth_place: birthPlace,
                    latitude: lat,
                    longitude: lon,
                    timezone: resolvedTimezone
                })
            });

            const data = await res.json();

            if (res.ok) {
                successEl.textContent = "Profile registered! Telemetry mapped successfully.";
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
            errorEl.textContent = err.message || "Cannot route automated telemetry data to deployment database.";
            errorEl.classList.remove("hidden");
        } finally {
            // Reset button states
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        }
    });

    // Handle logout/disconnect
    document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("celestial_token");
        showAuthGate();
    });
});

// UI Views Toggle Logic
function showAuthGate() {
    document.getElementById("auth-gate").classList.remove("hidden");
    document.getElementById("dashboard").classList.add("hidden");
}

function showDashboard() {
    document.getElementById("auth-gate").classList.add("hidden");
    document.getElementById("dashboard").classList.remove("hidden");
    fetchDailyForecast();
}

// Markdown Formatter Utility
class DailyForecastWorker {
    static formatMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-zinc-100 font-bold block text-base mt-4 mb-1">$1</strong>')
            .replace(/\n/g, '<br>');
    }
}

// API Data Fetching Loop
async function fetchDailyForecast() {
    const token = localStorage.getItem("celestial_token");
    const transitList = document.getElementById("transit-list");
    const horoscopeContent = document.getElementById("horoscope-content");
    const dateLabel = document.getElementById("forecast-date");

    try {
        const res = await fetch(`${API_BASE}/daily-forecast`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await res.json();

        if (res.status === 401) {
            localStorage.removeItem("celestial_token");
            showAuthGate();
            return;
        }

        dateLabel.textContent = data.date_today || "2026-05-22";

        transitList.innerHTML = "";
        if (data.active_geometric_transits && data.active_geometric_transits.length > 0) {
            data.active_geometric_transits.forEach(t => {
                const card = document.createElement("div");
                card.className = "transit-card p-3 rounded-lg text-xs space-y-1";
                
                const badgeColor = t.aspect === "Square" ? "text-red-400 bg-red-950/30 border-red-900/50" : "text-emerald-400 bg-emerald-950/30 border-emerald-900/50";
                
                card.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="font-semibold text-zinc-300">Moving ${t.transit_planet}</span>
                        <span class="px-2 py-0.5 border rounded-full text-[10px] uppercase font-mono ${badgeColor}">${t.aspect}</span>
                    </div>
                    <div class="text-zinc-500 font-medium">Hitting Natal <span class="text-zinc-300">${t.natal_planet}</span></div>
                    <div class="text-[10px] text-zinc-600 font-mono">Orb Variance: ${t.orb_variance}°</div>
                `;
                transitList.appendChild(card);
            });
        } else {
            transitList.innerHTML = `<p class="text-zinc-600 text-xs text-center py-4">No active geometric transits found.</p>`;
        }

        horoscopeContent.innerHTML = DailyForecastWorker.formatMarkdown(data.daily_horoscope);

    } catch (err) {
        horoscopeContent.innerHTML = `<p class="text-red-400 text-xs">Error parsing dynamic transit telemetry endpoint loop connection.</p>`;
    }
}