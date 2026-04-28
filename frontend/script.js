
function checkAuth() {
    const token = localStorage.getItem("access_token");
    if (token) {
        document.getElementById("auth-section").classList.add("hidden");
        document.getElementById("main-app").classList.remove("hidden");
        document.getElementById("logout-btn").classList.remove("hidden");
        loadUserInfo();
        testFetch();
    } else {
        document.getElementById("auth-section").classList.remove("hidden");
        document.getElementById("main-app").classList.add("hidden");
        document.getElementById("logout-btn").classList.add("hidden");
    }
}

async function loadUserInfo() {
    const response = await fetch("/me", {
        headers: { "Authorization": "Bearer " + localStorage.getItem("access_token") }
    });
    if (!response.ok) return;
    const data = await response.json();
    updateLangToggle(data.language || "en");
}

async function setLanguage(lang) {
    await fetch(`/me/language?language=${lang}`, {
        method: "PATCH",
        headers: { "Authorization": "Bearer " + localStorage.getItem("access_token") }
    });
    updateLangToggle(lang);
}

function updateLangToggle(lang) {
    const enBtn = document.getElementById("lang-en");
    const koBtn = document.getElementById("lang-ko");
    if (lang === "ko") {
        koBtn.classList.add("bg-gray-600", "text-white");
        koBtn.classList.remove("text-gray-400");
        enBtn.classList.remove("bg-gray-600", "text-white");
        enBtn.classList.add("text-gray-400");
    } else {
        enBtn.classList.add("bg-gray-600", "text-white");
        enBtn.classList.remove("text-gray-400");
        koBtn.classList.remove("bg-gray-600", "text-white");
        koBtn.classList.add("text-gray-400");
    }
}

function logout() {
    localStorage.removeItem("access_token");
    document.getElementById("food-grid").innerHTML = "";
    checkAuth();
}

let authMode = "login"

function showLogin() {
    authMode = "login"
    document.getElementById("login-tab").classList.add("bg-gray-600", "text-white")
    document.getElementById("login-tab").classList.remove("text-gray-400")
    document.getElementById("register-tab").classList.remove("bg-gray-600", "text-white")
    document.getElementById("register-tab").classList.add("text-gray-400")
    document.getElementById("auth-btn").textContent = "Login"
}

function showRegister() {
    authMode = "register"
    document.getElementById("register-tab").classList.add("bg-gray-600", "text-white")
    document.getElementById("register-tab").classList.remove("text-gray-400")
    document.getElementById("login-tab").classList.remove("bg-gray-600", "text-white")
    document.getElementById("login-tab").classList.add("text-gray-400")
    document.getElementById("auth-btn").textContent = "Register"
}

async function submitAuth() {
    const email = document.getElementById("auth-email").value;
    const password = document.getElementById("auth-password").value;
    const errorEl = document.getElementById("auth-error");
    errorEl.classList.add("hidden");

    if (authMode === "login") {
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username: email, password: password })
        });
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem("access_token", data.access_token);
            checkAuth();
        } else {
            errorEl.textContent = "Invalid email or password.";
            errorEl.classList.remove("hidden");
        }
    } else {
        const response = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, password: password })
        });
        if (response.ok) {
            authMode = "login";
            await submitAuth();
        } else {
            const data = await response.json();
            errorEl.textContent = data.detail || "Registration failed.";
            errorEl.classList.remove("hidden");
        }
    }
}


let currentOffset = 0

async function testFetch(append = false) {
    try {
        const searchTerm = document.getElementById("search-input").value;
        const response = await fetch(`/entries?label=${searchTerm}&offset=${currentOffset}&limit=10`, {
            method: "GET",
            headers: { "Authorization": "Bearer " + localStorage.getItem("access_token") },
        });
        if (!response.ok) {
            throw new Error("Could not fetch resource");
        }

        const data = await response.json();
        const gridContainer = document.getElementById("food-grid");

        if (!append) {
            currentOffset = 0;
            gridContainer.innerHTML = "";
        }


        
        const entries = data.entries;
        const groups = {};
        entries.forEach(food => {
            const date = new Date(food.logged_at + "Z").toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
            if (!groups[date]) groups[date] = [];
            groups[date].push(food);
        });

        Object.keys(groups).forEach(date => {
            const dailyTotal = groups[date].reduce((sum, f) => sum + (f.calories || 0), 0);
            const totalText = dailyTotal > 0 ? `<span class="text-gray-400 text-sm font-normal ml-3">${dailyTotal} kcal total</span>` : '';
            gridContainer.innerHTML += `<h2 class="col-span-full text-green-400 font-semibold text-lg border-b border-gray-700 pb-1 mt-4">${date}${totalText}</h2>`;
            groups[date].forEach(food => {
                gridContainer.innerHTML += `
                <div class="bg-gray-800 rounded-xl shadow-md overflow-hidden">
                    <img src="${food.image_path}" class="w-full h-40 object-cover">
                    <div class="p-3">
                        <h2 class="text-sm font-semibold text-white text-center">${food.final_label}</h2>
                        <p class="text-green-400 text-xs text-center">${food.calories ? food.calories + ' kcal' : ''}</p>
                        <p class="text-gray-500 text-xs text-center mt-0.5">${new Date(food.logged_at + "Z").toLocaleTimeString()}</p>
                        <button onclick="deleteFood(${food.id})"
                            class="mt-2 w-full border border-red-500 text-red-400 bg-transparent text-xs px-2 py-1 rounded hover:bg-red-500 hover:text-white transition">
                            Delete
                        </button>
                    </div>
                </div>`;
            });
        });

        const searchBox = document.getElementById("search-input");
        console.log(data);

        const loadMoreBtn = document.getElementById("load-more");
        if (data.has_next) {
            loadMoreBtn.classList.remove("hidden");
        } else {
            loadMoreBtn.classList.add("hidden");
        }

    } catch (error) {
        console.error("Fetch failed:", error);
    }
}
checkAuth()

function openSidebar() {
    document.getElementById("sidebar").classList.remove("-translate-x-full");
    document.getElementById("sidebar-overlay").classList.remove("hidden");
}

function closeSidebar() {
    document.getElementById("sidebar").classList.add("-translate-x-full");
    document.getElementById("sidebar-overlay").classList.add("hidden");
}

function setFileSelected(file) {
    const label = document.getElementById("file-label");
    const icon = document.getElementById("upload-icon");
    const nameEl = document.getElementById("file-name-text");
    const subEl = document.getElementById("file-sub-text");
    if (file) {
        label.classList.replace("border-gray-600", "border-green-500");
        icon.classList.replace("text-gray-500", "text-green-400");
        nameEl.textContent = file.name;
        nameEl.classList.replace("text-gray-400", "text-white");
        subEl.textContent = "Ready to upload";
        subEl.classList.replace("text-gray-600", "text-green-500");
    } else {
        label.classList.replace("border-green-500", "border-gray-600");
        icon.classList.replace("text-green-400", "text-gray-500");
        nameEl.textContent = "Click to upload image";
        nameEl.classList.replace("text-white", "text-gray-400");
        subEl.textContent = "JPG, PNG, WEBP, HEIC";
        subEl.classList.replace("text-green-500", "text-gray-600");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("file-input").addEventListener("change", function() {
        setFileSelected(this.files[0] || null);
    });
});

async function deleteFood(id){
    if (!confirm("Delete this entry?")) return;
    const response = await fetch(`/entries/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + localStorage.getItem("access_token") }
    });
    testFetch();
}

async function uploadFood() {
    const button = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");
    const labelInput = document.getElementById("label-input");

    const file = fileInput.files[0];
    if (!file) {
        alert("Please choose an image first!");
        return;
    }

    button.textContent = "Identifying food...";
    button.disabled = true;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("final_label", labelInput.value);

    const errorEl = document.getElementById("upload-error");
    const response = await fetch("/uploads", {
        method: "POST",
        headers: { "Authorization": "Bearer " + localStorage.getItem("access_token") },
        body: formData
    });

    button.textContent = "Upload Food";
    button.disabled = false;

    if (!response.ok) {
        const data = await response.json();
        errorEl.textContent = data.detail || "Upload failed.";
        errorEl.classList.remove("hidden");
        return;
    }

    errorEl.classList.add("hidden");
    closeSidebar();
    showToast();
    fileInput.value = "";
    labelInput.value = "";
    setFileSelected(null);
    currentOffset = 0;
    testFetch();
}

function openPasswordModal() {
    document.getElementById("current-password").value = "";
    document.getElementById("new-password").value = "";
    document.getElementById("confirm-password").value = "";
    document.getElementById("password-error").classList.add("hidden");
    document.getElementById("password-modal").classList.remove("hidden");
}

function closePasswordModal() {
    document.getElementById("password-modal").classList.add("hidden");
}

async function changePassword() {
    const currentPwd = document.getElementById("current-password").value;
    const newPwd = document.getElementById("new-password").value;
    const confirmPwd = document.getElementById("confirm-password").value;
    const errorEl = document.getElementById("password-error");

    if (newPwd !== confirmPwd) {
        errorEl.textContent = "New passwords do not match.";
        errorEl.classList.remove("hidden");
        return;
    }

    const response = await fetch("/me/password", {
        method: "PATCH",
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("access_token"),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ current_password: currentPwd, new_password: newPwd })
    });

    if (!response.ok) {
        const data = await response.json();
        errorEl.textContent = data.detail || "Failed to change password.";
        errorEl.classList.remove("hidden");
        return;
    }

    closePasswordModal();
    showToast("Password changed successfully!");
}

function showToast(message = "Uploaded successfully!") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.remove("opacity-0");
    toast.classList.add("opacity-100");
    setTimeout(() => {
        toast.classList.remove("opacity-100");
        toast.classList.add("opacity-0");
    }, 2500);
}

function switchTab(tab) {
    const isJournal = tab === "journal";
    document.getElementById("journal-view").classList.toggle("hidden", !isJournal);
    document.getElementById("summary-view").classList.toggle("hidden", isJournal);
    document.getElementById("tab-journal").className = `px-4 py-1.5 rounded-md text-sm font-medium transition ${isJournal ? "bg-gray-600 text-white" : "text-gray-400 hover:text-white"}`;
    document.getElementById("tab-summary").className = `px-4 py-1.5 rounded-md text-sm font-medium transition ${!isJournal ? "bg-gray-600 text-white" : "text-gray-400 hover:text-white"}`;
    if (!isJournal) loadSummary(7);
}

let calorieChart = null;

async function loadSummary(days) {
    // Update range button styles
    document.getElementById("range-7").className = `px-4 py-1.5 rounded-full text-sm font-medium transition ${days === 7 ? "bg-green-600 text-white" : "bg-gray-700 text-gray-400 hover:text-white"}`;
    document.getElementById("range-30").className = `px-4 py-1.5 rounded-full text-sm font-medium transition ${days === 30 ? "bg-green-600 text-white" : "bg-gray-700 text-gray-400 hover:text-white"}`;

    const response = await fetch(`/entries/summary?days=${days}`, {
        headers: { "Authorization": "Bearer " + localStorage.getItem("access_token") }
    });
    if (!response.ok) return;
    const data = await response.json();

    const labels = data.map(d => new Date(d.date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }));
    const calories = data.map(d => d.calories);

    if (calorieChart) calorieChart.destroy();

    Chart.register(ChartDataLabels);
    const ctx = document.getElementById("calorie-chart").getContext("2d");
    calorieChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Calories (kcal)",
                data: calories,
                backgroundColor: "rgba(34, 197, 94, 0.6)",
                borderColor: "rgba(34, 197, 94, 1)",
                borderWidth: 1,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#9ca3af" } },
                datalabels: {
                    anchor: "end",
                    align: "top",
                    color: "#ffffff",
                    font: { weight: "bold", size: 12 },
                    formatter: (value) => value + " kcal"
                }
            },
            scales: {
                x: { ticks: { color: "#9ca3af" }, grid: { color: "#374151" } },
                y: { ticks: { color: "#9ca3af" }, grid: { color: "#374151" }, beginAtZero: true }
            }
        }
    });
}

function loadMore() {
    currentOffset += 10;
    testFetch(append = true);
}

