async function testFetch() {
    try {
        const response = await fetch("http://127.0.0.1:8000/entries");
        if(!response.ok){
            throw new Error("Could not fetch resource");
        }

        const data = await response.json();
        const gridContainer = document.getElementById("food-grid");
        gridContainer.innerHTML = "";
        const entries = data.entries;
        entries.forEach(food => {
            const cardHTML = `
                <div class="bg-white rounded-lg shadow-md p-4">
                    <img src="${ food.image_url }" class="w-full h-48 object-cover rounded-md mb-4">
                    
                    <h2 class="text-xl font-semibold text-gray-800 text-center">${ food.final_label }</h2>
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