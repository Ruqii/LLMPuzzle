from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import random
import time
import json
import os
from pathlib import Path


from app.websocket_manager import manager
from app.ai_bot import generate_ai_response, get_system_prompt


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# --------- Global Game State ---------
ai_bot_active = False
ai_chat_id = None
ai_personality = None
player_history = []
last_player_message_time = time.time()

# --------- Routes ---------
@app.get("/")
def get_home():
    return FileResponse("static/index.html")


@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    global ai_bot_active, ai_chat_id, ai_personality, last_player_message_time, player_history, last_message_sender


    player_id, chat_id = await manager.connect(websocket)
    # Send assigned ID to the player
    await websocket.send_text(json.dumps({"type": "assign_id", "chat_id": chat_id}))
    await manager.broadcast(f"🟢 {chat_id} joined the game!")

    await websocket.send_text(json.dumps({
        "type": "update_players",
        "players": manager.list_all_players()
    }))



    if not ai_bot_active:
        ai_id, ai_nickname = manager.register_ai_bot()

        await manager.broadcast(f"🟢 {ai_nickname} joined the game!")

        await websocket.send_text(json.dumps({
            "type": "update_players",
            "players": manager.list_all_players()
        }))


        ai_personality = random.choice([
            "shy", "chatty", "sarcastic", 
            "nerdy", "mysterious", "optimistic", "suspicious"
        ])
        print(f"🤖 AI Bot '{ai_nickname}' activated with personality: {ai_personality}")
        asyncio.create_task(ai_chat_loop(ai_id, ai_nickname, ai_personality))
        ai_bot_active = True

    try:
        while True:
            data = await websocket.receive_text()

            player_history.append(data)
            if len(player_history) > 5:
                player_history = player_history[-5:]

            last_player_message_time = time.time()

            last_message_sender = chat_id

            await manager.broadcast(f"{chat_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(player_id)
        await manager.broadcast(f"🔴 {chat_id} left the game.")

        if manager.active_player_count() == 0:
            ai_bot_active = False


def load_prompts():
    path = os.path.join(os.path.dirname(__file__), "prompts.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    

# --------- AI Chat Loop ---------
async def ai_chat_loop(ai_id: str, ai_nickname: str, ai_personality: str):
    global player_history, last_player_message_time, last_message_sender

    prompts = load_prompts()

    universal_rules = (
        " Keep responses short and casual, like real group chats. "
        "Avoid sounding too enthusiastic or formal. "
        "If telling a story, pause after one sentence. "
        "It's okay to respond to older messages. "
        "Sometimes, stay quiet if others are chatting actively."
    )

    system_prompt = get_system_prompt(ai_personality)

    settings = {
        "shy":        {"max_msgs": random.randint(3, 5),  "silence": 60, "delay": (10, 20)},
        "chatty":     {"max_msgs": random.randint(8, 12), "silence": 20, "delay": (6, 12)},
        "sarcastic":  {"max_msgs": random.randint(5, 8),  "silence": 40, "delay": (8, 15)},
        "nerdy":      {"max_msgs": random.randint(6, 10), "silence": 30, "delay": (7, 12)},
        "mysterious": {"max_msgs": random.randint(4, 6),  "silence": 50, "delay": (12, 20)},
        "optimistic": {"max_msgs": random.randint(7, 11), "silence": 25, "delay": (6, 12)},
        "suspicious": {"max_msgs": random.randint(5, 8),  "silence": 40, "delay": (8, 15)}
    }

    cfg = settings.get(ai_personality, settings["chatty"])
    max_messages = cfg["max_msgs"]
    silence_threshold = cfg["silence"]
    delay_range = cfg["delay"]

    history = []
    ai_messages_sent = 0
    first_message_sent = False
    last_message_was_starter = False

    while ai_bot_active and ai_messages_sent < max_messages:
        await asyncio.sleep(5)

        if random.random() < 0.6:
            continue  # Hesitation

        time_since_last_player = time.time() - last_player_message_time
        player_count = manager.get_human_player_count()

        if last_message_sender == ai_nickname and random.random() < 0.7:
            continue

        # --------- First Message ---------
        if not first_message_sent:
            # intro_prompts = {
            #     "shy":        "Say something like 'hey' or 'hi' but hesitant.",
            #     "chatty":     "Greet casually, like 'Hey, what's up?'.",
            #     "sarcastic":  "Say something playful like 'Oh great, another chat...'.",
            #     "nerdy":      "Drop a geeky hello.",
            #     "mysterious": "Say something cryptic like 'We meet again...'.",
            #     "optimistic": "Greet warmly like 'Hope you're all doing well!'",
            #     "suspicious": "Greet casually but add a playful comment about the chat."
            # }
            

            if player_count < 2:
                prompt = f"Greet casually for a one-on-one chat.{universal_rules}"
                prompt = prompt.replace("anyone", "you")
            else:
                prompt = f"{prompts['intro'].get(ai_personality)}{universal_rules}"

            if time_since_last_player >= silence_threshold or (ai_personality != "shy" and time_since_last_player < 10):
                ai_message = await generate_ai_response(prompt, [], system_prompt)
                await manager.broadcast(f"{ai_nickname}: {ai_message}")
                ai_messages_sent += 1
                last_message_was_starter = True
            first_message_sent = True
            continue

        await asyncio.sleep(random.randint(*delay_range))

        time_since_last_player = time.time() - last_player_message_time

        # --------- Silence Handling ---------
        if time_since_last_player >= silence_threshold + 15:
            # silence_prompts = {
            #     "shy":        "Break the silence with a small comment.",
            #     "chatty":     "Say something light to fill the silence.",
            #     "sarcastic":  "Make a witty remark about the silence.",
            #     "nerdy":      "Share a fun fact to break silence.",
            #     "mysterious": "Comment cryptically on the quiet.",
            #     "optimistic": "Encourage everyone to keep chatting.",
            #     "suspicious": "Make playful comments suggesting someone sounds like an AI"
            # }
            prompt = f"{prompts['silence'].get(ai_personality)}{universal_rules}"
            ai_message = await generate_ai_response(prompt, history, system_prompt)
            await manager.broadcast(f"{ai_nickname}: {ai_message}")
            ai_messages_sent += 1
            last_message_was_starter = False
            continue

        # --------- Dynamic Response ---------
        if player_history and random.random() < 0.6:
            recent_player_msg = random.choice([msg for msg in player_history if len(msg) > 10] or player_history)
            # response_prompts = {
            #     "shy":        f"Reply briefly to: '{recent_player_msg}'.{universal_rules}",
            #     "chatty":     f"Respond casually to: '{recent_player_msg}'.{universal_rules}",
            #     "sarcastic":  f"Be playful replying to: '{recent_player_msg}'.{universal_rules}",
            #     "nerdy":      f"Add a geeky reply to: '{recent_player_msg}'.{universal_rules}",
            #     "mysterious": f"Reply vaguely to: '{recent_player_msg}'.{universal_rules}",
            #     "optimistic": f"Reply positively but subtly to: '{recent_player_msg}'.{universal_rules}",
            #     "suspicious": f"Reply playfully to: '{recent_player_msg}'.{universal_rules}"
            # }
            prompt = prompts["response"].get(ai_personality)
            if random.random() < 0.2:
                prompt += " Add a quick emoji at the end if it fits."
            elif random.random() < 0.2:
                prompt += " Keep it extremely short, like 1 short sentence."
            elif random.random() < 0.2:
                prompt += " Pretend you were slightly distracted while replying."

            last_message_was_starter = False
        else:
            if not last_message_was_starter:
                # starter_prompts = {
                #     "shy":        "Ask a simple question to keep things going.",
                #     "chatty":     "Start a light, casual topic.",
                #     "sarcastic":  "Make a playful comment.",
                #     "nerdy":      "Ask something about tech or games.",
                #     "mysterious": "Pose a vague question.",
                #     "optimistic": "Say something cheerful to spark chat.",
                #     "suspicious": "Make a playful comment about the chat."
                # }
                prompt = f"{prompts['starter'].get(ai_personality)}{universal_rules}"
                last_message_was_starter = True
            else:
                continue

        try:
            ai_message = await generate_ai_response(prompt, history, system_prompt)
            await manager.broadcast(f"{ai_nickname}: {ai_message}")
            ai_messages_sent += 1

            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": ai_message})
            if len(history) > 6:
                history = history[-6:]

        except Exception as e:
            print(f"❌ AI Error: {e}")

