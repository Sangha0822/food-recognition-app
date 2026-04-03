async function testFetch() {
    try {
        const response = await fetch("http://127.0.0.1:8000/entries");
        if (!response.ok) {
            throw new Error("Could not fetch resource");
        }

        const data = await response.json();
        const gridContainer = document.getElementById("food-grid");
        gridContainer.innerHTML = "";
        const entries = data.entries;
        entries.forEach(food => {
            const cardHTML = `
                <div class="bg-white rounded-lg shadow-md p-4">
                    <img src="${food.image_url}" class="w-full h-48 object-cover rounded-md mb-4">
                    
                    <h2 class="text-xl font-semibold text-gray-800 text-center">${food.final_label}</h2>
                </div>
            `;
            gridContainer.innerHTML += cardHTML;
        });

        const searchBox = document.getElementById("search-input");
        console.log(data);
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
    testFetch();
}