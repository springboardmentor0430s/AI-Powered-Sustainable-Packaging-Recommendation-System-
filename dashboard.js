document.getElementById("packagingForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    console.log("Form submitted with data:", data);

    try {
        // API call to ML backend
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        console.log("Response status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        console.log("Prediction result:", result);

        // Store prediction data in sessionStorage for analysis page
        const analysisData = {
            ...data,
            ...result
        };
        console.log("Analysis data to store:", analysisData);
        sessionStorage.setItem('analysisData', JSON.stringify(analysisData));

        // Redirect to analysis page
        console.log("Redirecting to /analysis");
        setTimeout(() => {
            window.location.href = '/analysis';
        }, 500);
    } catch (error) {
        console.error("Error:", error);
        alert("Error: " + error.message);
    }
});
