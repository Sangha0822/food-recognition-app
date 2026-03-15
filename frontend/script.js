async function testFetch() {
    try {
        const response = await fetch("https://pokeapi.co/api/v2/pokemon/charizard");
        const data = await response.json(); // Don't forget to unbox the JSON!
        console.log(data);
    } catch (error) {
        console.error("Fetch failed:", error);
    }
}
testFetch();