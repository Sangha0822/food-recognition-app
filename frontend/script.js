
function checkAuth() {
    const token = localStorage.getItem("access_token");
    if (token) {
        document.getElementById("auth-section").classList.add("hidden");
        document.getElementById("main-app").classList.remove("hidden");
        document.getElementById("logout-btn").classList.remove("hidden");
        testFetch();
    } else {
        document.getElementById("auth-section").classList.remove("hidden");
        document.getElementById("main-app").classList.add("hidden");
        document.getElementById("logout-btn").classList.add("hidden");
    }
}

function logout() {
    localStorage.removeItem("access_token");
    checkAuth();
}

let authMode = "login"

function showLogin() {
    authMode = "login"
    document.getElementById("login-tab").classList.add("text-green-400", "font-semibold", "border-b-2", "border-green-400")
    document.getElementById("login-tab").classList.remove("text-gray-400")
    document.getElementById("register-tab").classList.remove("text-green-400", "font-semibold", "border-b-2", "border-green-400")
    document.getElementById("register-tab").classList.add("text-gray-400")
    document.getElementById("auth-btn").textContent = "Login"
}

function showRegister() {
    authMode = "register"
    document.getElementById("register-tab").classList.add("text-green-400", "font-semibold", "border-b-2", "border-green-400")
    document.getElementById("register-tab").classList.remove("text-gray-400")
    document.getElementById("login-tab").classList.remove("text-green-400", "font-semibold", "border-b-2", "border-green-400")
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
            errorEl.textContent = "Registration failed. Email may already exist.";
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
        entries.forEach(food => {
            const cardHTML = `
        <div class="bg-gray-800 rounded-lg shadow-md p-4">
            <img src="${food.image_url}" class="w-full h-48 object-cover rounded-md mb-4">
            <h2 class="text-lg font-semibold text-white text-center">${food.final_label}</h2>
            <p class="text-gray-500 text-xs text-center mt-1">${new Date(food.logged_at).toLocaleString()}</p>
            <button onclick="deleteFood(${food.id})"
                class="mt-2 w-full border border-red-500 text-red-400 bg-transparent text-xs px-2 py-1 rounded hover:bg-red-500 hover:text-white transition">
                Delete
            </button>
            </div>
            `;
            
            gridContainer.innerHTML += cardHTML;
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


async function deleteFood(id){
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
    fileInput.value = "";
    currentOffset = 0;
    testFetch();
}

function loadMore() {
    currentOffset += 10;
    testFetch(append = true);
}

