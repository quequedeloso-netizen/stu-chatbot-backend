import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from faq_data import get_faq_answer

load_dotenv()

# Assuming OPENAI_API_KEY is in the environment
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dynamic Knowledge Map
STU_BASE_URL = "https://www.stu.edu.tw/"
KNOWLEDGE_MAP = {}

def fetch_stu_links():
    """
    Scrapes the STU homepage on startup to dynamically build a link repository.
    This creates an immediate baseline of accurate URLs for the chatbot to use.
    """
    print("Fetching dynamic links from STU website...")
    try:
        response = requests.get(STU_BASE_URL, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all link elements
        links = soup.find_all('a', href=True)
        count = 0
        
        for link in links:
            text = link.get_text(strip=True)
            href = link['href']
            
            # Skip empty text or purely JS links
            if not text or href.startswith('javascript:'):
                continue
                
            # Normalize URLs
            if href.startswith('/'):
                href = STU_BASE_URL.rstrip('/') + href
            elif not href.startswith('http'):
                continue # Skip mailto or other relative paths that are complex
                
            # Add to map using the link text as the key (lowercased for uniform searching)
            if len(text) > 2: # Ignore very short link text
                KNOWLEDGE_MAP[text.lower()] = href
                count += 1
                
        print(f"Successfully scraped {count} dynamic links from STU homepage.")
    except Exception as e:
        print(f"Failed to scrape STU links: {e}")

# Run the scraper once when the module loads
fetch_stu_links()

async def process_message(message: str, history: list, language: str) -> dict:
    """
    Process the user message using a Hybrid System:
    1. Check FAQ Database and Dynamic Links (No API)
    2. Fallback to OpenAI if no match is found
    """
    
    # --- HYBRID SYSTEM: FAQ & LINK MATCHING ---
    # This part is Fast, Cheap, and No API required
    direct_response = get_faq_answer(message, KNOWLEDGE_MAP)
    if direct_response:
        return direct_response
    
    # --- AI FALLBACK ---
    # We serialize a subset of the knowledge map if it's too large, but for a homepage it's usually < 200 links
    # which is well within the token limit.
    safe_links = json.dumps(KNOWLEDGE_MAP, ensure_ascii=False)
    
    system_prompt = f"""
    You are an intelligent university chatbot for Shu-Te University (https://www.stu.edu.tw/).
    Your goal is to provide students with direct, fast, and accurate access to information.
    
    CRITICAL RULE:
    1. Every time a student asks to access specific information (like grades, scholarships, schedules, portal, etc.), you MUST explicitly tell them to log into the portal.
    2. Provide this exact portal login link: https://info.stu.edu.tw/ePortal/login.asp
    3. You must provide the portal link using your exact words: "Please log in to the portal using your school ID number and password: https://info.stu.edu.tw/ePortal/login.asp" 
    
    You also have access to the following dynamically scraped links directly from the STU website to provide as additional context:
    {safe_links}
    
    Output Format:
    You must output a raw JSON object with exactly two keys:
    {{
       "text": "Your complete helpful response in {language}, including HTML formatted links.",
       "translation": "If {language} is NOT 'zh-tw' or 'zh-cn', this field MUST contain the exact Taiwanese Mandarin (zh-tw) translation of your text. Otherwise, leave it empty."
    }}
    Do not wrap the JSON in markdown blocks like ```json. Just output the raw JSON object.
    
    Instructions:
    1. Analyze the intent. If it's about student info, give the portal link provided above.
    2. Search the scraped links for relevant STU pages.
    3. Make sure links in your `text` are full URLs.
    4. Provide the correct `text` in {language}.
    5. Always provide the `translation` in Traditional Chinese (zh-tw) if the requested language is foreign.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Format history if any, capped at last 5 turns to save tokens
    recent_history = history[-5:] if len(history) > 5 else history
    for msg in recent_history:
        role = "user" if msg.get("sender") == "user" else "assistant"
        text = msg.get("text", "")
        if text:
            messages.append({"role": role, "content": text})
            
    # Add the current message
    messages.append({"role": "user", "content": message})
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=500
        )
        answer_str = response.choices[0].message.content.strip()
        
        import json
        
        # safely parse json from string
        if answer_str.startswith("```json"):
            answer_str = answer_str.replace("```json", "").replace("```", "").strip()
            
        try:
            parsed = json.loads(answer_str)
            return {
                "text": parsed.get("text", answer_str),
                "translation": parsed.get("translation", "")
            }
        except json.JSONDecodeError:
            # fallback if it didn't output json
            return {
                "text": answer_str,
                "translation": ""
            }
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        fallback = "Sorry, I am having trouble connecting to my brain right now. Please visit https://www.stu.edu.tw/"
        return {
            "text": fallback,
            "translation": ""
        }
