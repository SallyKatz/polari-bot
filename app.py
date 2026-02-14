from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import random
import re
import os

app = Flask(__name__)

# Authentic historical Polari vocabulary (1950s-1960s British gay slang)
# Based on comprehensive dictionary
POLARI = {
    # Core vocabulary from dictionary
    "face": "eek", "mouth": "muns", "eyes": "ogles", "head": "bonce",
    "money": "dinarly", "food": "manjarry", "drink": "bevvy", "house": "cottage",
    "man": "omi", "woman": "palone", "policeman": "charpering omi", "prison": "nick",
    "bed": "cot", "shoes": "batts", "clothes": "drag", "hat": "capella", "hair": "riah",
    "hands": "lappers", "legs": "lallies", "feet": "plates", "child": "feely",
    "friend": "bencove", "stranger": "gajo", "ring": "martini", "jewelry": "groinage",
    "car": "cabouche", "road": "streeta", "door": "entry", "window": "winda",
    "table": "mesa", "chair": "sessa", "dog": "buppy", "cat": "pussy",
    "song": "cantata", "voice": "voche", "word": "lav", "name": "moniker",
    "see": "varda", "look": "varda", "eat": "mungaree", "go": "vaggerie", "walk": "troll",
    "make love": "charver", "kiss": "lamor", "touch": "fumble", "steal": "shush",
    "arrest": "charper", "hit": "schonk", "run away": "scarper", "stop": "nist",
    "sleep": "letty", "die": "cark it", "good": "bona", "bad": "naff", "big": "large",
    "small": "bijou", "old": "auld", "beautiful": "bona", "ugly": "naff",
    "crazy": "meshigener", "drunk": "bevvied", "tired": "jaded", "sick": "ogue",
    "alone": "on your tod", "together": "toge", "none": "nanti", "many": "multy",
    "very": "multy", "not": "nanti", "here": "here", "now": "now", "later": "after",
    "never": "nanti", "always": "always", "yes": "yes", "no": "nanti",
    "please": "prees", "thank you": "thank you", "hello": "boyno", "goodbye": "cheerio",
    "excuse me": "scuse", "nothing": "nanti", "something": "somewhat",
    "everything": "all", "everyone": "omi-palone", "gay man": "omi-palone",
    "lesbian": "palone-omee", "sex": "arva", "penis": "bagaga", "vagina": "clevie",
    "breasts": "jubes", "attractive": "bona", "terrible": "cod", "wonderful": "fantabulosa",
    "toilet": "carsey", "telephone": "dog and bone", "water": "aqua", "gin": "vera",
    "pub": "bevvy ken", "shop": "bodega", "sailor": "barkey", "police": "lilly",
    "judge": "beak", "fight": "barney", "talk": "cackle", "sing": "chant",
    "write": "screeve", "read": "read", "know": "savvy", "understand": "savvy",
    "feel": "reef", "give": "lend", "take": "lell", "have": "hav",
    "make": "make", "do": "do", "say": "say", "think": "think",
    "get": "get", "come": "order", "leave": "vaggerie", "wait": "wait",
    "find": "find", "tell": "tell", "ask": "ask", "work": "work",
    "play": "jogger", "dance": "wallop", "crazy person": "meshigener",
    "young person": "feely", "old person": "badge cove", "rich person": "duchess",
    "poor person": "nanti dinarly", "friend": "sister", "lover": "husband",
    "stranger": "gajo", "enemy": "enemy", "party": "do", "bar": "bevvy ken",
    "restaurant": "carnish ken", "street": "streeta", "room": "booth",
    "mirror": "vardavision", "watch": "timepiece", "umbrella": "gamp",
    "handkerchief": "fogle", "cigarette": "vogue", "drugs": "dubes",
    "morning": "journo", "night": "nochy", "day": "journo", "today": "today",
    "tomorrow": "tomorrow", "yesterday": "yesterday", "soon": "soon",
    "quickly": "quickly", "slowly": "slowly", "well": "bona", "badly": "naffly",
    "easily": "easily", "hard": "hard", "soft": "soft", "hot": "hot",
    "cold": "cold", "new": "new", "clean": "clean", "dirty": "mungey",
    "happy": "bona", "sad": "naff", "angry": "dander", "tired": "jaded",
    "sick": "ogue", "afraid": "afraid", "surprised": "surprised", "ready": "ready",
    "sure": "sure", "maybe": "maybe", "probably": "probably", "definitely": "definitely",
    "actually": "your actual", "really": "really", "only": "only", "just": "just",
    "also": "also", "too": "too", "enough": "enough", "almost": "almost",
    "even": "even", "still": "still", "already": "already", "yet": "yet",
    "again": "again", "back": "back", "forward": "forward", "up": "up",
    "down": "down", "in": "in", "out": "out", "on": "on", "off": "off",
    "over": "over", "under": "under", "through": "through", "between": "between",
    "before": "before", "after": "after", "during": "during", "without": "nanti",
    "about": "about", "against": "against", "among": "among", "around": "around",
    "at": "at", "by": "by", "for": "for", "from": "from", "of": "of",
    "to": "to", "with": "with", "within": "within", "without": "nanti"
}

POLARI_WORDS = set(POLARI.values())

# WHITELIST - Add your friends' numbers here (with country code)
WHITELIST = {
    "+447967277970",  # Your number
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
    
    # Level 0-2: Mostly English with a hint of Polari
    if level <= 2:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "boyno"]):
            return "Coo-ee. Bona to varda your eek."
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly here, palone. I'm skint."
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry", "mungaree"]):
            return "I'm dying for some manjarry. Let's mungaree."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll", "vaggerie"]):
            return "I'll troll along with you. Let's vaggerie."
        elif any(x in msg_lower for x in ["drink", "bevvy", "pub", "bar"]):
            return "Fancy a bevvy at the bevvy ken?"
        elif any(x in msg_lower for x in ["what are you up to", "doing", "up to"]):
            return "Just trolling the streeta. Varda-ing the omis."
        elif any(x in msg_lower for x in ["how are you", "how you doing"]):
            return "Bona. Nanti naff, omi-palone."
        elif any(x in msg_lower for x in ["who are you", "your name"]):
            return "Just an omi. Varda my eek and you'll savvy."
        elif any(x in msg_lower for x in ["good", "great", "fantastic", "bona"]):
            return "Fantabulosa! That's bona."
        elif any(x in msg_lower for x in ["bad", "terrible", "awful", "naff", "cod"]):
            return "Cod! That's naff."
        elif any(x in msg_lower for x in ["police", "cop", "charpering omi", "lilly"]):
            return "Watch out for the charpering omi. The lilly is about."
        elif any(x in msg_lower for x in ["sex", "fuck", "shag", "charver", "arva"]):
            return "Looking for some arva? You're a bold one."
        elif any(x in msg_lower for x in ["love", "like", "fancy"]):
            return "You're a bit of trade. I might fancy you."
        elif any(x in msg_lower for x in ["where", "place", "location", "cottage", "ken"]):
            return "Let's find a cottage. Or my ken is nearby."
        elif any(x in msg_lower for x in ["clothes", "wear", "dress", "drag", "schmutter"]):
            return "I love your schmutter. Is that full drag?"
        elif any(x in msg_lower for x in ["hair", "wig", "riah", "shyckle", "poll"]):
            return "Your riah is fantabulosa. Is that a shyckle?"
        elif any(x in msg_lower for x in ["legs", "lallies", "pins"]):
            return "Varda the lallies on you. Bona lallies."
        elif any(x in msg_lower for x in ["face", "eek", "muns", "ogles"]):
            return "You've got a bona eek. And your ogles are sparkling."
        elif any(x in msg_lower for x in ["party", "fun", "night out", "do"]):
            return "Let's have a do. It'll be fantabulosa."
        elif any(x in msg_lower for x in ["tired", "sleep", "bed", "letty", "cot"]):
            return "I'm jaded. Need to letty in my cot."
        elif any(x in msg_lower for x in ["drunk", "wasted", "bevvied", "palare"]):
            return "I'm bevvied. Had too much bevvy."
        else:
            return random.choice([
                "Savvy?",
                "Nanti problem.",
                "Varda that.",
                "Bona."
            ])
    
    # Level 3-5: Mixed English/Polari
    elif level <= 5:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "boyno"]):
            return "Boyno. Bona to varda your eek, omi-palone."
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly. I'm on my tod and skint."
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry", "mungaree"]):
            return "Let's mungaree some manjarry. I'm famished."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll", "vaggerie"]):
            return "We'll troll the streeta. Vaggerie to the cottage."
        elif any(x in msg_lower for x in ["drink", "bevvy", "pub", "bar"]):
            return "Fancy a bevvy? The bevvy ken is calling."
        elif any(x in msg_lower for x in ["what are you up to", "doing", "up to"]):
            return "Trolling the streeta, varda-ing trade. Savvy?"
        elif any(x in msg_lower for x in ["how are you", "how you doing"]):
            return "Bona. Nanti naff. Yourself, palone?"
        elif any(x in msg_lower for x in ["who are you", "your name"]):
            return "An omi-palone. Varda my eek and savvy."
        elif any(x in msg_lower for x in ["good", "great", "fantastic", "bona"]):
            return "Fantabulosa! That's your actual bona."
        elif any(x in msg_lower for x in ["bad", "terrible", "awful", "naff", "cod"]):
            return "Cod! That's naff. Don't be strange."
        elif any(x in msg_lower for x in ["police", "cop", "charpering omi", "lilly"]):
            return "Charpering omi alert. The lilly is varda-ing us."
        elif any(x in msg_lower for x in ["sex", "fuck", "shag", "charver", "arva"]):
            return "After some arva? You're bold. Fancy a charver?"
        elif any(x in msg_lower for x in ["love", "like", "fancy"]):
            return "You're bona trade. I fancy your lallies."
        elif any(x in msg_lower for x in ["where", "place", "location", "cottage", "ken"]):
            return "My ken is bijou but cosy. Or find a cottage."
        elif any(x in msg_lower for x in ["clothes", "wear", "dress", "drag", "schmutter"]):
            return "Your schmutter is bona. Full drag?"
        elif any(x in msg_lower for x in ["hair", "wig", "riah", "shyckle", "poll"]):
            return "Bona riah. Is that a shyckle or your actual?"
        elif any(x in msg_lower for x in ["legs", "lallies", "pins"]):
            return "Varda your lallies. Bona lallies, palone."
        elif any(x in msg_lower for x in ["face", "eek", "muns", "ogles"]):
            return "Bona eek. Your ogles are fantabulosa."
        elif any(x in msg_lower for x in ["party", "fun", "night out", "do"]):
            return "Let's have a do. Bring your bevvy."
        elif any(x in msg_lower for x in ["tired", "sleep", "bed", "letty", "cot"]):
            return "I'm jaded. Need to letty in my cot."
        elif any(x in msg_lower for x in ["drunk", "wasted", "bevvied", "palare"]):
            return "Bevvied again. The bevvy was flowing."
        else:
            return random.choice([
                "Savvy, palone?",
                "Nanti problem, omi.",
                "Varda that, sister.",
                "Bona. Nanti naff."
            ])
    
    # Level 6-8: Mostly Polari
    elif level <= 8:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "boyno"]):
            return "Boyno. Bona to varda your eek. How's your voche?"
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly. The charpering omi might varda."
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry", "mungaree"]):
            return "Mungaree manjarry at the carnish ken. Bona."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll", "vaggerie"]):
            return "Troll to the cottage. Nanti scarper."
        elif any(x in msg_lower for x in ["drink", "bevvy", "pub", "bar"]):
            return "Bevvy at the bevvy ken? I'm gasping."
        elif any(x in msg_lower for x in ["what are you up to", "doing", "up to"]):
            return "Trolling the streeta, varda-ing trade. Savvy?"
        elif any(x in msg_lower for x in ["how are you", "how you doing"]):
            return "Bona. Nanti naff. And you, omi-palone?"
        elif any(x in msg_lower for x in ["who are you", "your name"]):
            return "Omi-palone. Varda my eek and savvy."
        elif any(x in msg_lower for x in ["good", "great", "fantastic", "bona"]):
            return "Fantabulosa! Your actual bona."
        elif any(x in msg_lower for x in ["bad", "terrible", "awful", "naff", "cod"]):
            return "Cod! Naff. Don't be strange."
        elif any(x in msg_lower for x in ["police", "cop", "charpering omi", "lilly"]):
            return "Charpering omi! The lilly is varda-ing. Scarper!"
        elif any(x in msg_lower for x in ["sex", "fuck", "shag", "charver", "arva"]):
            return "After arva? Bold. Fancy a charver in the cottage?"
        elif any(x in msg_lower for x in ["love", "like", "fancy"]):
            return "You're bona trade. I fancy your lallies and eek."
        elif any(x in msg_lower for x in ["where", "place", "location", "cottage", "ken"]):
            return "My ken is bijou. Or find a cottage for arva."
        elif any(x in msg_lower for x in ["clothes", "wear", "dress", "drag", "schmutter"]):
            return "Bona schmutter. Full drag? Zhoosh your riah."
        elif any(x in msg_lower for x in ["hair", "wig", "riah", "shyckle", "poll"]):
            return "Bona riah. Shyckle or actual? Zhoosh it."
        elif any(x in msg_lower for x in ["legs", "lallies", "pins"]):
            return "Varda the lallies. Bona. Fancy a feel?"
        elif any(x in msg_lower for x in ["face", "eek", "muns", "ogles"]):
            return "Bona eek. Your ogles are fantabulosa."
        elif any(x in msg_lower for x in ["party", "fun", "night out", "do"]):
            return "Let's have a do. Fantabulosa! Bring bevvy."
        elif any(x in msg_lower for x in ["tired", "sleep", "bed", "letty", "cot"]):
            return "Jaded. Need to letty in my cot."
        elif any(x in msg_lower for x in ["drunk", "wasted", "bevvied", "palare"]):
            return "Bevvied. The bevvy was bona."
        else:
            return random.choice([
                "Savvy, omi-palone?",
                "Nanti naff.",
                "Varda that.",
                "Bona. Troll careful."
            ])
    
    # Level 9-10: Full Polari
    else:
        if any(x in msg_lower for x in ["hello", "hi", "hey", "boyno"]):
            return "Boyno. Bona to varda your eek. How's your voche? Troll safe."
        elif any(x in msg_lower for x in ["money", "cash", "pay", "dinarly"]):
            return "Nanti dinarly? The charpering omi might varda. Scarper!"
        elif any(x in msg_lower for x in ["food", "eat", "hungry", "manjarry", "mungaree"]):
            return "Mungaree manjarry at the carnish ken. Bona, nanti naff."
        elif any(x in msg_lower for x in ["go", "leave", "walk", "troll", "vaggerie"]):
            return "Troll to the cottage. Nanti scarper. The streeta is meshigener."
        elif any(x in msg_lower for x in ["drink", "bevvy", "pub", "bar"]):
            return "Bevvy at the bevvy ken? I'm gasping for a vera."
        elif any(x in msg_lower for x in ["what are you up to", "doing", "up to"]):
            return "Trolling the streeta, varda-ing trade and omis. Savvy?"
        elif any(x in msg_lower for x in ["how are you", "how you doing"]):
            return "Bona. Nanti naff. Yourself, omi-palone?"
        elif any(x in msg_lower for x in ["who are you", "your name"]):
            return "Omi-palone. Varda my eek and savvy my polari."
        elif any(x in msg_lower for x in ["good", "great", "fantastic", "bona"]):
            return "Fantabulosa! Your actual bona. Mental!"
        elif any(x in msg_lower for x in ["bad", "terrible", "awful", "naff", "cod"]):
            return "Cod! Naff. Don't be strange, palone."
        elif any(x in msg_lower for x in ["police", "cop", "charpering omi", "lilly"]):
            return "Charpering omi! The lilly is varda-ing. Scarper to the cottage!"
        elif any(x in msg_lower for x in ["sex", "fuck", "shag", "charver", "arva"]):
            return "After arva? Bold omi. Fancy a charver? Full harva?"
        elif any(x in msg_lower for x in ["love", "like", "fancy"]):
            return "You're bona trade. I fancy your lallies, eek, and all."
        elif any(x in msg_lower for x in ["where", "place", "location", "cottage", "ken"]):
            return "My ken is bijou. Or find a cottage for arva. Nanti charpering omi."
        elif any(x in msg_lower for x in ["clothes", "wear", "dress", "drag", "schmutter"]):
            return "Bona schmutter. Full drag? Zhoosh your riah and ogles."
        elif any(x in msg_lower for x in ["hair", "wig", "riah", "shyckle", "poll"]):
            return "Bona riah. Shyckle or actual? Zhoosh it, palone."
        elif any(x in msg_lower for x in ["legs", "lallies", "pins"]):
            return "Varda the lallies. Bona. Fancy a reef?"
        elif any(x in msg_lower for x in ["face", "eek", "muns", "ogles"]):
            return "Bona eek. Your ogles are fantabulosa. Zhoosh your riah."
        elif any(x in msg_lower for x in ["party", "fun", "night out", "do"]):
            return "Let's have a do. Fantabulosa! Bring bevvy and trade."
        elif any(x in msg_lower for x in ["tired", "sleep", "bed", "letty", "cot"]):
            return "Jaded. Need to letty in my cot. Nanti more bevvy."
        elif any(x in msg_lower for x in ["drunk", "wasted", "bevvied", "palare"]):
            return "Bevvied. The bevvy was bona. I'm palare."
        else:
            return random.choice([
                "Savvy, omi-palone?",
                "Nanti naff. All bona.",
                "Varda that. Fantabulosa.",
                "Bona. Troll careful on the streeta."
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
