# FAQ Database for STU Chatbot

FAQ_DATABASE = {
    "portal": {
        "text": "Please log in to the portal using your school ID number and password: https://info.stu.edu.tw/ePortal/login.asp",
        "keywords": ["portal", "login", "grades", "eportal", "sign in", "student id", "sis"]
    },
    "location": {
        "text": "Shu-Te University is located at No. 18, Hunghua Rd., Yanchao Dist., Kaohsiung City 82445, Taiwan (R.O.C.).",
        "keywords": ["location", "address", "address of school", "campus location", "how to get there"]
    },
    "repairs": {
        "text": "To report a dorm repair or any campus maintenance issue, please log in to the <b>ePortal</b> (https://info.stu.edu.tw/ePortal/login.asp), go to 'General Affairs Management' -> 'Online Repair System', and submit a repair request.",
        "keywords": ["repair", "fix", "dorm repair", "broken", "maintenance", "reconstruction"]
    },
    "grades": {
        "text": "You can check your grades and academic records by logging into the <b>STU Academic Services Portal</b> here: <a href='https://infosys.stu.edu.tw/AcademicServices/Grade' target='_blank'>Check My Grades</a>.",
        "keywords": ["grades", "grade", "score", "scores", "results", "academic results", "how are my grades"]
    },
    "contact": {
        "text": "You can contact STU at +886-7-6158000. For more specific department contacts, please visit: https://www.stu.edu.tw/category/about-stu/contact-us/",
        "keywords": ["contact", "phone", "number", "email", "call", "telephone", "office"]
    },
    "admissions": {
        "text": "For information about admissions, please visit the STU Admissions page: https://english.stu.edu.tw/admissions/",
        "keywords": ["admissions", "apply", "enroll", "how to join", "new student", "requirement"]
    },
    "scholarships": {
        "text": "Information about scholarships can be found on our financial aid page: https://www.stu.edu.tw/category/student-affairs/scholarships/",
        "keywords": ["scholarship", "financial aid", "grant", "money", "funding", "bursary"]
    },
    "library": {
        "text": "The STU Library provides various resources. You can access the library website here: https://lib.stu.edu.tw/",
        "keywords": ["library", "books", "study", "research", "journal"]
    },
    "international": {
        "text": "For international students, please check the Office of International and Cross-Strait Affairs: https://oia.stu.edu.tw/",
        "keywords": ["international", "foreign", "exchange", "overseas"]
    }
}

import re

def get_faq_answer(message: str, knowledge_map: dict = None) -> dict:
    """
    Checks if the user message matches any FAQ keywords or scraped links.
    Returns a response dict or None.
    """
    message = message.lower()
    
    # Check manual FAQ first
    for key, data in FAQ_DATABASE.items():
        for keyword in data["keywords"]:
            # Pattern matches the keyword as a whole word (using word boundaries \b)
            pattern = re.compile(rf'\b{re.escape(keyword.lower())}\b')
            if pattern.search(message):
                return {
                    "text": data["text"],
                    "translation": "" 
                }
    
    # Check scraped link map (KNOWLEDGE_MAP)
    if knowledge_map:
        # Sort keys by length descending to match the most specific link first
        sorted_keys = sorted(knowledge_map.keys(), key=len, reverse=True)
        for text in sorted_keys:
            href = knowledge_map[text]
            # If the user mentions a specific section of the site (at least 5 chars)
            if text in message and len(text) > 4: 
                return {
                    "text": f"I found a relevant link for you: <a href='{href}' target='_blank'>{text.capitalize()}</a>",
                    "translation": ""
                }
                
    return None
