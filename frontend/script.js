async function testFetch() {
    try {
        const response = await fetch("http://127.0.0.1:8000/entries");
        if(!response.ok){
            throw new Error("Could not fetch resource");
        }
        
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error("Fetch failed:", error);
    }
}
testFetch();