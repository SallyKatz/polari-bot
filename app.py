from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import random
import re
import os

app = Flask(__name__)

# Authentic historical Polari vocabulary (1950s-1960s British gay slang)
POLARI = {
    "face": "eek", "mouth": "muns", "eyes": "ogles", "head": "bonce",
    "money": "dinarly", "food": "manjarry", "drink": "buvare", "house": "cottage",
    "man": "omi", "woman": "palone", "policeman": "charpering omi", "prison": "nick",
    "bed": "cot", "shoes": "batts", "clothes": "drag", "hat": "lid", "hair": "feathers",
    "hands": "mitt", "legs": "lallies", "feet": "trotters", "child": "nanti",
    "friend": "bev", "stranger": "strill", "ring": "fingering", "jewelry": "fakement",
    "car": "motor", "road": "streeta", "door": "entry", "window": "winda",
    "table": "mesa", "chair": "sessa", "dog": "buppy", "cat": "pussy",
    "song": "cantata", "voice": "voker", "word": "varda", "name": "moniker",
    "see": "varda", "look": "varda", "eat": "munge", "go": "troll", "walk": "troll",
    "make love": "charver", "kiss": "chivvy", "touch": "fumble", "steal": "nick",
    "arrest": "charper", "hit": "chiv", "run away": "scarper", "stop": "nist",
    "sleep": "slumber", "die": "go", "good": "bona", "bad": "naff", "big": "large",
    "small": "tottie", "old": "auld", "beautiful": "bona", "ugly": "naff",
    "crazy": "meshigener", "drunk": "palare", "tired": "jaded", "sick": "ogue",
    "alone": "sola", "together": "toge", "none": "nanti", "many": "much",
    "very": "very", "not": "nanti", "here": "here", "now": "now", "later": "after",
    "never": "nanti", "always": "always", "yes": "yes", "no": "nanti",
    "please": "prees", "thank you": "thank you", "hello": "bona",
    "goodbye": "cheerio", "excuse me": "scuse", "nothing": "nanti",
    "something": "somewhat", "everything": "all", "everyone": "omi-palone"
}

POLARI_WORDS = set(POLARI.values())

# WHITELIST - Add your friends' numbers here (with country code)
WHITELIST = {
    "+447967277970",  # Your number (I can see it in your screenshot)
    # Add friends like: "+447123456789",
}

# Track each contact's Polari level (0-10)
contact_levels = {}

def get_polari_ratio(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    polari_count = sum(1 for word in words if word in POLARI_WORDS)
    return polari_count / len(words)

def update_level(number, message):
    current_level = contact_levels.get(number, 0)
    ratio = get_polari_ratio(message)
    
    if ratio > 0.3:
        new_level = min(10, current_level + 2)
    elif ratio > 0:
        new_level = min(10, current_level + 1)
    else:
        new_level = max(0, current_level - 1)
    
    contact_levels[number] = new_level
    return new_level

def generate_response(level, message):
    msg_lower = message.lower()
    
    # Level 0-2: Mostly English
    if level <= 2:
        if any(x in msg_lower for x in ["hello", "hi", "hey"]):
            return "Coo-ee. Bona to varda your eek."
        elif any(x in msg_lower for x in ["money", "cash", "pay"]):
            return "No money here."
        elif any(x in msg_lower for x in ["food", "eat", "hungry"]):
            return "Get some food."
        elif any(x in msg_lower for x in ["go", "leave", "walk"]):
            return "Go carefully."
        else:
            return random.choice(["Yes, I understand.", "What do you need?", "I am here.", "Speak clearly."])
    
    # Level 3-5: Mixed English/Polari
    elif level <= 5:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "bona"]):
            return "Bona to varda your eek."
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly here. No money."
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry"]):
            return "Munge some manjarry. Eat food."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll"]):
            return "Troll careful. Walk safe."
        else:
            return random.choice(["Bona eek. Good face.", "Nanti problem. No trouble.", "Varda that. Look there.", "All is bona. All is good."])
    
    # Level 6-8: Mostly Polari
    elif level <= 8:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "bona"]):
            return "Bona to varda your eek. How's the voker?"
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly. The charpering omi might varda."
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry"]):
            return "Munge manjarry at the caff. Bona lally."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll"]):
            return "Troll to the cottage. Nanti scarper."
        else:
            return random.choice(["Varda the lallies on that omi.", "Nanti naff, all bona.", "Munge and bevare.", "Troll careful on the streeta."])
    
    # Level 9-10: Full Polari
    else:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "bona"]):
            return "Bona to varda your eek. How's your voker? Troll safe on the streeta."
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly? The charpering omi might varda you. Scarper if you varda the blue."
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry"]):
            return "Munge some manjarry at the caff. Bona lally, nanti naff."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll"]):
            return "Troll to the cottage. Nanti scarper. The streeta is meshigener tonight."
        else:
            return random.choice([
                "Varda the lallies on that omi. Bona feathers, naff drag.",
                "Nanti naff, all bona. The omi-palone are toge.",
                "Munge and bevare. The charpering omi troll here.",
                "Troll careful on the streeta. Nanti varda the blue.",
                "Bona vardering. The ogles are bona, the muns is tottie."
            ])

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    from_number = request.values.get('From', '').replace('whatsapp:', '')
    body = request.values.get('Body', '')
    
    # CONTACT FILTERING: Only respond to whitelisted numbers
    if from_number not in WHITELIST:
        return "", 204  # Silent drop for non-whitelisted
    
    # POLARI DETECTION: Update level based on message content
    level = update_level(from_number, body)
    
    # Generate response based on level
    response_text = generate_response(level, body)
    
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(response_text)
    
    return str(resp)

@app.route("/")
def health():
    return "Polari bot running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


