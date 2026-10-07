const stateEl = document.getElementById("state");
const transcriptEl = document.getElementById("transcript");
const responseEl = document.getElementById("response");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const micButton = document.getElementById("micButton");

function setState(value) {
    stateEl.textContent = value.toUpperCase();
    document.body.classList.remove("listening", "thinking", "speaking");
    if (["LISTENING", "THINKING", "SPEAKING"].includes(value.toUpperCase())) {
        document.body.classList.add(value.toLowerCase());
    }
}

function showResult(transcript, response) {
    transcriptEl.textContent = transcript || "Command completed.";
    responseEl.textContent = response || "";
}

async function sendText(message, speak = false) {
    const text = message.trim();
    if (!text) return;

    transcriptEl.textContent = text;
    responseEl.textContent = "";
    setState("THINKING");

    try {
        const result = await fetch("/api/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: text, speak})
        });

        const data = await result.json();
        showResult(text, data.response || "No response.");
        setState(speak ? "SPEAKING" : "READY");

        if (speak) {
            setTimeout(() => setState("READY"), 1600);
        }
    } catch (error) {
        responseEl.textContent = "Connection to Synora failed.";
        setState("ERROR");
    }
}

async function voiceCommand() {
    setState("LISTENING");
    transcriptEl.textContent = "Listening...";
    responseEl.textContent = "Speak naturally. Synora is listening.";

    try {
        const listen = await fetch("/api/voice/listen", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: "{}"
        });

        const data = await listen.json();

        if (!data.success || !data.transcript) {
            transcriptEl.textContent = "No speech detected.";
            responseEl.textContent = "Try again.";
            setState("READY");
            return;
        }

        const transcript = data.transcript;
        transcriptEl.textContent = transcript;
        setState("THINKING");
        responseEl.textContent = "Processing command...";

        const result = await fetch("/api/voice/respond", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: transcript})
        });

        const answer = await result.json();
        responseEl.textContent = answer.response || "Command completed.";
        setState("SPEAKING");
        setTimeout(() => setState("READY"), 1800);
    } catch (error) {
        responseEl.textContent = "Voice request failed.";
        setState("ERROR");
    }
}

sendButton.addEventListener("click", () => sendText(input.value, false));

input.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendText(input.value, false);
        input.value = "";
    }
});

micButton.addEventListener("click", voiceCommand);

document.querySelectorAll("[data-command]").forEach(button => {
    button.addEventListener("click", () => {
        const command = button.dataset.command;
        input.value = command;
        sendText(command, false);
    });
});

setState("READY");
