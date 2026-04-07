let currentOffset = 0

async function testFetch(append = false) {
    try {
        const searchTerm = document.getElementById("search-input").value;
        const response = await fetch(`http://127.0.0.1:8000/entries?label=${searchTerm}&offset=${currentOffset}&limit=10`);
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
testFetch();

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

    const response = await fetch("http://127.0.0.1:8000/uploads", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    console.log("Uploaded!", data);
    button.textContent = "Upload Food";
    button.disabled = false;
    currentOffset = 0;
    testFetch();
}

function loadMore() {
    currentOffset += 10;
    testFetch(append = true);
}