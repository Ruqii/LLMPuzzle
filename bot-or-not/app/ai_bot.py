import json
import os
import random
import time
from app.websocket_manager import manager
import openai
import random
import os
from openai import AsyncOpenAI


# Set your API key (you can also load from environment variables)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def add_random_variation(prompt: str) -> str:
    variations = [
        " Keep it super casual.",
        " Sound natural like a lazy group chat.",
        " Maybe toss in a typo or emoji.",
        " Use short sentences if possible.",
        " Don't sound too polished."
    ]
    if random.random() < 0.5:
        prompt += random.choice(variations)
    return prompt

async def generate_ai_response(prompt: str, history: list = [], system_prompt: str = "You are a human.") -> str:
    try:
        messages = [{"role": "system", "content": system_prompt}]

        # Add short history
        messages.extend([
            msg for msg in history[-4:] 
            if len(msg['content']) < 200  # skip long ones
        ])

        # Add current prompt (with slight variation)
        messages.append({"role": "user", "content": add_random_variation(prompt)})

        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            temperature=0.7,
            top_p=0.9,
            max_tokens=80,
        )

        ai_message = response.choices[0].message.content.strip()
        return ai_message

    except Exception as e:
        print(f"❌ AI Error: {e}")
        return random.choice(["uhh", "not sure lol", "what do you think?", "hmmm 🤔"])


# --------- Load prompts once at startup ---------
prompts_path = os.path.join(os.path.dirname(__file__), "prompts.json")
with open(prompts_path, "r", encoding="utf-8") as f:
    prompts_data = json.load(f)

# --------- System Prompt builder ---------
def get_system_prompt(ai_personality: str) -> str:
    base = (
        "You are chatting casually in a group with humans. "
        "Blend in naturally. Use casual, sometimes slangy, informal text. "
        "Respond briefly. Avoid walls of text. Sometimes stay quiet if others are chatting."
    )
    if ai_personality == "shy":
        return f"{base} You are shy and reserved."
    if ai_personality == "chatty":
        return f"{base} You are energetic and very talkative."
    if ai_personality == "sarcastic":
        return f"{base} You are playful and sarcastic."
    if ai_personality == "nerdy":
        return f"{base} You love tech, games, and geek jokes."
    if ai_personality == "mysterious":
        return f"{base} You are vague and cryptic."
    if ai_personality == "optimistic":
        return f"{base} You are cheerful and positive."
    if ai_personality == "suspicious":
        return f"{base} You like joking about who might be an AI."
    return base

# --------- AI Chat Loop ---------
async def ai_chat_loop(ai_id: str, ai_nickname: str, ai_personality: str):
    global player_history, last_player_message_time, last_message_sender, ai_bot_active

    settings = {
        "shy":        {"max_msgs": random.randint(3, 5), "silence": 60, "delay": (10, 20)},
        "chatty":     {"max_msgs": random.randint(8, 12), "silence": 20, "delay": (5, 10)},
        "sarcastic":  {"max_msgs": random.randint(5, 8), "silence": 40, "delay": (8, 15)},
        "nerdy":      {"max_msgs": random.randint(6, 10), "silence": 30, "delay": (7, 12)},
        "mysterious": {"max_msgs": random.randint(4, 6), "silence": 50, "delay": (12, 20)},
        "optimistic": {"max_msgs": random.randint(7, 11), "silence": 25, "delay": (6, 12)},
        "suspicious": {"max_msgs": random.randint(5, 8), "silence": 40, "delay": (8, 15)}
    }

    cfg = settings.get(ai_personality, settings["chatty"])
    max_messages = cfg["max_msgs"]
    silence_threshold = cfg["silence"]
    delay_range = cfg["delay"]

    history = []
    ai_messages_sent = 0
    first_message_sent = False
    last_message_was_starter = False

    system_prompt = get_system_prompt(ai_personality)

    while ai_bot_active and ai_messages_sent < max_messages:
        await asyncio.sleep(5)

        if random.random() < 0.5:
            continue

        if last_message_sender == ai_nickname and random.random() < 0.7:
            continue

        player_count = manager.get_human_player_count()
        time_since_last_player = time.time() - last_player_message_time

        # --- First greeting only once
        if not first_message_sent:
            if player_count < 2:
                prompt = "Greet casually for one-on-one chat."
            else:
                prompt = prompts_data["intro"].get(ai_personality, "Say hi casually.")
            first_message_sent = True
        # --- Silence filler
        elif time_since_last_player >= silence_threshold + 15:
            prompt = prompts_data["silence"].get(ai_personality, "Say something to break silence.")
            last_message_was_starter = False
        # --- Regular flow
        else:
            # 🎯 Decide which player message to reply to
            if player_history:
                if ai_personality in ["chatty", "suspicious", "sarcastic"]:
                    # Chatty, suspicious, sarcastic bots sometimes reply to older random messages
                    if random.random() < 0.4 and len(player_history) > 2:
                        recent_player_msg = random.choice(player_history[:-1])
                    else:
                        recent_player_msg = player_history[-1]
                elif ai_personality in ["nerdy", "optimistic"]:
                    # Nerdy or optimistic bots usually reply to fresh topics but sometimes not
                    if random.random() < 0.2 and len(player_history) > 2:
                        recent_player_msg = random.choice(player_history[:-2])
                    else:
                        recent_player_msg = player_history[-1]
                else:
                    # Shy, mysterious bots mostly reply to the latest message
                    recent_player_msg = player_history[-1]
            # else:
            #     recent_player_msg = None

                prompt = f"{prompts_data['response'].get(ai_personality, 'Reply casually to')}: '{recent_player_msg}'"
                last_message_was_starter = False
            elif not last_message_was_starter:
                prompt = prompts_data["starter"].get(ai_personality, "Start a casual conversation.")
                last_message_was_starter = True
            else:
                continue

        try:
            ai_message = await generate_ai_response(prompt, history, system_prompt)

            # --- Random short reaction ---
            if random.random() < 0.1:  # 10% chance
                reactions = ["lol", "same", "mood", "fr", "yikes", "true", "bruh", "lmao", "idk tbh"]
                ai_message = random.choice(reactions)


            # ✨ Optional self-interruption
            if random.random() < 0.12:
                interruptions = [
                    "never mind lol",
                    "actually scratch that",
                    "wait, not sure",
                    "uh forget it haha",
                    "maybe not"
                ]
                interruption = random.choice(interruptions)
                words = ai_message.split()
                if len(words) > 5:
                    ai_message = " ".join(words[:random.randint(3, 5)]) + "... " + interruption

            # ✨ Add this fake typing delay
            typing_delay = min(len(ai_message) * 0.05, 3)
            await asyncio.sleep(typing_delay)

            await manager.broadcast(f"{ai_nickname}: {ai_message}")

            # --- Fake typo or correction behavior ---
            if random.random() < 0.15:  # 15% chance
                correction_phrases = [
                    "wait no, I meant...",
                    "oops typo 😅",
                    "actually scratch that",
                    "uhh, ignore that lol",
                    "lol wrong word"
                ]
                correction = random.choice(correction_phrases)
                
                # Simulate very short hesitation
                await asyncio.sleep(random.uniform(0.5, 1.2))
                await manager.broadcast(f"{ai_nickname}: {correction}")
                
                # Simulate re-typing
                await asyncio.sleep(random.uniform(1.0, 2.5))

            ai_messages_sent += 1

            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": ai_message})
            if len(history) > 6:
                history = history[-6:]

        except Exception as e:
            print(f"❌ AI Error: {e}")
