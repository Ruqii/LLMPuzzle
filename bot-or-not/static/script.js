let myChatId = "";
let hasVoted = false;

const socket = new WebSocket(`ws://${location.host}/ws/game`);

const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const votingOptions = document.getElementById("votingOptions");

socket.onopen = function() {
    console.log("✅ Connected");
};


// --- WebSocket Events ---
socket.onopen = function() {
    console.log("✅ Connected to game server");
};

socket.onmessage = function(event) {
    let data = event.data;

    try {
        const jsonData = JSON.parse(data);

        if (jsonData.type === "assign_id") {
            myChatId = jsonData.chat_id;
            document.getElementById("nicknameDisplay").innerText = `You are: ${myChatId}`;
            return;
        }

        if (jsonData.type === "voting_start") {
            setupVotingButtons(jsonData.players);
            startChatTimer(120);  // 2 minutes chat phase
            return;
        }

        if (jsonData.type === "voting_result") {
            showVotingResult(jsonData);
            return;
        }

        if (jsonData.type === "update_players") {
            setupVotingButtons(jsonData.players);
            return;
        }
        

    } catch (e) {
        // Not a JSON message, treat as chat
    }

    chatBox.innerHTML += `<p>${data}</p>`;
    chatBox.scrollTop = chatBox.scrollHeight;
};

socket.onclose = function() {
    console.log("🔌 Disconnected from server");
};

// --- Send Chat Message ---
messageInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter" && messageInput.value.trim() !== "" && !hasVoted) {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(messageInput.value);
            messageInput.value = "";
        }
    }
});

// --- Setup Voting Buttons (Visible During Chat) ---
function setupVotingButtons(players) {
    const votingOptions = document.getElementById("votingOptions");
    votingOptions.innerHTML = "<p>🕵️ Vote when you're ready:</p>";

    players.forEach(player => {
        let btn = document.createElement("button");
        btn.innerText = player;
        btn.className = "vote-button";

        // 🔹 This is where you add the onclick function!
        btn.onclick = function() {
            if (!hasVoted && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: "vote", vote_for: player }));
                votingOptions.innerHTML = `<p>✅ You voted for ${player}. Waiting for results...</p>`;
                hasVoted = true;

                // Disable chat input
                messageInput.disabled = true;

                // Visually close the chat window
                chatBox.classList.add("chat-closed");
            }
        };

        votingOptions.appendChild(btn);
    });
}

// --- Chat Countdown Timer ---
function startChatTimer(seconds) {
    let timerDisplay = document.createElement("p");
    timerDisplay.id = "chatTimerDisplay";
    document.getElementById("votingArea").prepend(timerDisplay);

    let timeLeft = seconds;
    let timerInterval = setInterval(() => {
        timerDisplay.innerText = `⏳ Chat ends in ${timeLeft} seconds`;
        timeLeft--;

        if (timeLeft < 0) {
            clearInterval(timerInterval);
            chatBox.classList.add("chat-closed");

            messageInput.disabled = true;
            chatBox.innerHTML += "<p>⏰ Chat time is over! If you haven't voted, please vote below.</p>";

            if (!hasVoted) {
                // Only add warning if it's not already there
                if (!document.getElementById("voteReminder")) {
                    let reminder = document.createElement("p");
                    reminder.id = "voteReminder";
                    reminder.innerText = "⚠️ Please click a button to vote!";
                    votingOptions.appendChild(reminder);
                }
            }
        }
    }, 1000);
}


// --- Display Voting Result ---
function showVotingResult(resultData) {
    const { winner, ai_nickname } = resultData;

    votingOptions.innerHTML = `
        <p>🎭 The AI was: <b>${ai_nickname}</b></p>
        <p>🏆 ${winner} win!</p>
    `;
    messageInput.disabled = true;

    // Optionally, gray out chat box
    chatBox.classList.add("chat-closed");
}


function handleVote(player) {
    if (!hasVoted && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "vote", vote_for: player }));
        hasVoted = true;

        document.querySelectorAll('.vote-button').forEach(btn => btn.disabled = true);
        votingOptions.innerHTML += `<p>✅ You voted for ${player}. Waiting for others...</p>`;
        messageInput.disabled = true;
    }
}

