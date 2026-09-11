async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const chatHistory = document.getElementById("chat-history");
    const message = inputField.value.trim();
    
    if (!message) return;

    // 1. Add User Message
    const userDiv = document.createElement("div");
    userDiv.className = "user-msg";
    userDiv.textContent = message;
    chatHistory.appendChild(userDiv);
    
    inputField.value = "";
    
    // 2. Add Loading Indicator
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "bot-msg text-muted";
    loadingDiv.innerHTML = "<em>Thinking...</em>";
    chatHistory.appendChild(loadingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        // 3. Send to Flask Server
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // 4. Safely Remove Loading Indicator
        loadingDiv.remove();

        // 5. Render Bot Answer
        const botDiv = document.createElement("div");
        botDiv.className = "bot-msg";
        
        if (data.response) {
            // Check if the marked library loaded successfully
            if (typeof marked !== 'undefined') {
                botDiv.innerHTML = marked.parse(data.response);
            } else {
                // If the library was blocked, just show plain text!
                botDiv.innerText = data.response;
            }
        } else {
            botDiv.className = "bot-msg text-danger";
            botDiv.textContent = "Error: " + (data.error || "Unknown error");
        }
        
        chatHistory.appendChild(botDiv);

    } catch (error) {
        // We now print the EXACT error directly into the chat UI so it can't hide from us!
        loadingDiv.remove();
        const errorDiv = document.createElement("div");
        errorDiv.className = "bot-msg text-danger";
        errorDiv.textContent = "Javascript Crashed: " + error.message;
        chatHistory.appendChild(errorDiv);
    }
    
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function handleEnter(event) {
    if (event.key === "Enter") sendMessage();
}