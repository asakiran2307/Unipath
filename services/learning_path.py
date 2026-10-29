"""
Learning Path — curated video resources + mini-quiz per skill module.
Follows a Video → Quiz → Video → Quiz cycle (like Cisco Academy).
"""

# ── Curated Learning Resources by Skill ───────────────────────────────────────
# All videos are YouTube embeds (nocookie domain for privacy)

LEARNING_RESOURCES = {
    "Python": {
        "video_id": "rfscVS0vtbw",
        "title": "Python for Beginners — Full Course",
        "channel": "freeCodeCamp.org",
        "duration": "4 hours",
        "description": "Complete Python fundamentals: syntax, data types, functions, OOP, file I/O, and error handling. Perfect for absolute beginners.",
        "what_you_learn": ["Variables & Data Types", "Functions & Loops", "OOP Concepts", "File Handling", "Libraries & Modules"],
    },
    "JavaScript": {
        "video_id": "hdI2bqOjy3c",
        "title": "JavaScript Crash Course for Beginners",
        "channel": "Traversy Media",
        "duration": "1.5 hours",
        "description": "Learn modern JavaScript: ES6+, DOM manipulation, async/await, fetch API, and more.",
        "what_you_learn": ["Variables & Functions", "DOM Manipulation", "ES6+ Features", "Async/Await", "Fetch API"],
    },
    "React": {
        "video_id": "bMknfKXIFA8",
        "title": "React Course — Full Tutorial for Beginners",
        "channel": "freeCodeCamp.org",
        "duration": "10 hours",
        "description": "Build real React apps from scratch: hooks, state management, routing, and API integration.",
        "what_you_learn": ["JSX & Components", "useState & useEffect", "Props & State", "React Router", "API Calls"],
    },
    "Machine Learning": {
        "video_id": "Gv9_4yMHFhI",
        "title": "Machine Learning for Everybody",
        "channel": "freeCodeCamp.org",
        "duration": "3.5 hours",
        "description": "ML fundamentals without the math overload: regression, classification, clustering, neural networks.",
        "what_you_learn": ["Supervised Learning", "Regression & Classification", "k-Means Clustering", "Neural Networks Intro", "Model Evaluation"],
    },
    "Data Science": {
        "video_id": "ua-CiDNNj30",
        "title": "Data Science Full Course for Beginners",
        "channel": "Simplilearn",
        "duration": "6 hours",
        "description": "Complete data science roadmap: NumPy, Pandas, Matplotlib, and ML with scikit-learn.",
        "what_you_learn": ["NumPy & Pandas", "Data Visualization", "Data Cleaning", "Exploratory Analysis", "ML with Scikit-learn"],
    },
    "DSA": {
        "video_id": "8hly31xKli0",
        "title": "Data Structures & Algorithms — Full Course",
        "channel": "freeCodeCamp.org",
        "duration": "8 hours",
        "description": "All major data structures and algorithms with visual explanations and code examples.",
        "what_you_learn": ["Arrays & Linked Lists", "Stacks & Queues", "Trees & Graphs", "Sorting Algorithms", "Dynamic Programming"],
    },
    "SQL": {
        "video_id": "HXV3zeQKqGY",
        "title": "SQL Full Course — Learn SQL in 4 Hours",
        "channel": "freeCodeCamp.org",
        "duration": "4.5 hours",
        "description": "Complete SQL from basic SELECT queries to advanced JOINs, subqueries, and window functions.",
        "what_you_learn": ["SELECT & WHERE", "JOINs (INNER/LEFT/RIGHT)", "GROUP BY & HAVING", "Subqueries", "Indexes & Optimization"],
    },
    "Java": {
        "video_id": "eIrMbAQSU34",
        "title": "Java Full Course — Beginner to Advanced",
        "channel": "Amigoscode",
        "duration": "4 hours",
        "description": "Java programming fundamentals: OOP, collections, streams, exceptions, and build tools.",
        "what_you_learn": ["OOP Principles", "Collections Framework", "Streams & Lambda", "Exception Handling", "Maven/Gradle"],
    },
    "C++": {
        "video_id": "vLnPwxZdW4Y",
        "title": "C++ Full Course for Beginners",
        "channel": "Bro Code",
        "duration": "6 hours",
        "description": "C++ from scratch: pointers, memory management, STL, and OOP with practical projects.",
        "what_you_learn": ["Pointers & References", "Memory Management", "STL Containers", "OOP in C++", "Templates"],
    },
    "HTML/CSS": {
        "video_id": "G3e-cpL7ofc",
        "title": "HTML & CSS Full Course — Beginner to Pro",
        "channel": "SuperSimpleDev",
        "duration": "6.5 hours",
        "description": "Build real websites from scratch with pure HTML and CSS including Flexbox, Grid, and responsive design.",
        "what_you_learn": ["HTML Structure", "CSS Selectors & Box Model", "Flexbox & Grid", "Responsive Design", "CSS Animations"],
    },
    "Node.js": {
        "video_id": "Oe421EPjeBE",
        "title": "Node.js Crash Course",
        "channel": "Traversy Media",
        "duration": "1.5 hours",
        "description": "Build REST APIs with Node.js and Express from scratch.",
        "what_you_learn": ["Node.js Basics", "Express Framework", "REST API Design", "Middleware", "File System & HTTP"],
    },
    "Docker": {
        "video_id": "fqMOX6JJhGo",
        "title": "Docker Tutorial for Beginners",
        "channel": "freeCodeCamp.org",
        "duration": "2 hours",
        "description": "Learn Docker containers, images, Docker Compose, and container orchestration basics.",
        "what_you_learn": ["Docker Concepts", "Images & Containers", "Dockerfile", "Docker Compose", "Networking & Volumes"],
    },
    "Git": {
        "video_id": "RGOj5yH7evk",
        "title": "Git and GitHub Crash Course",
        "channel": "freeCodeCamp.org",
        "duration": "1 hour",
        "description": "Master Git fundamentals: commits, branches, merges, pull requests, and collaboration workflows.",
        "what_you_learn": ["Init & Commit", "Branching & Merging", "Remote Repositories", "Pull Requests", "Resolving Conflicts"],
    },
    "TypeScript": {
        "video_id": "30LWjhZzg50",
        "title": "TypeScript Course for Beginners",
        "channel": "Academind",
        "duration": "3 hours",
        "description": "Learn TypeScript: types, interfaces, generics, decorators, and integration with React.",
        "what_you_learn": ["Types & Interfaces", "Generics", "Enums & Tuples", "Decorators", "TypeScript with React"],
    },
    "Flutter": {
        "video_id": "1ukSR1GRtMU",
        "title": "Flutter Course for Beginners",
        "channel": "freeCodeCamp.org",
        "duration": "3.7 hours",
        "description": "Build beautiful cross-platform mobile apps with Flutter and Dart.",
        "what_you_learn": ["Dart Basics", "Widgets & Layouts", "State Management", "Navigation", "API Integration"],
    },
    "DevOps": {
        "video_id": "j5Zsa_eOXeY",
        "title": "DevOps Engineering Course for Beginners",
        "channel": "freeCodeCamp.org",
        "duration": "2.5 hours",
        "description": "CI/CD pipelines, infrastructure as code, monitoring, and cloud deployment.",
        "what_you_learn": ["CI/CD Pipelines", "GitHub Actions", "Infrastructure as Code", "Monitoring & Alerts", "Cloud Deployment"],
    },
    "AWS": {
        "video_id": "ubCNZFQZZbI",
        "title": "AWS Cloud Practitioner — Full Exam Course",
        "channel": "freeCodeCamp.org",
        "duration": "11 hours",
        "description": "Complete AWS services overview: EC2, S3, RDS, Lambda, IAM, and cloud best practices.",
        "what_you_learn": ["EC2 & S3", "RDS & DynamoDB", "Lambda (Serverless)", "IAM & Security", "VPC & Networking"],
    },
    "TensorFlow": {
        "video_id": "tPYj3fFJGjk",
        "title": "TensorFlow 2.0 Complete Course",
        "channel": "freeCodeCamp.org",
        "duration": "7 hours",
        "description": "Deep learning with TensorFlow 2: neural networks, CNNs, RNNs, NLP, and model deployment.",
        "what_you_learn": ["Tensors & Operations", "Neural Networks", "CNNs & Image Classification", "RNNs & Time Series", "Model Deployment"],
    },
    "PyTorch": {
        "video_id": "Z_ikDlimN6A",
        "title": "PyTorch for Deep Learning — Full Course",
        "channel": "freeCodeCamp.org",
        "duration": "25 hours",
        "description": "Build deep learning models with PyTorch: tensors, autograd, CNNs, and transfer learning.",
        "what_you_learn": ["Tensors & Autograd", "Neural Networks", "CNNs", "Transfer Learning", "Model Training"],
    },
    "Cybersecurity": {
        "video_id": "hXSFdwIOfnE",
        "title": "Ethical Hacking Full Course",
        "channel": "freeCodeCamp.org",
        "duration": "15 hours",
        "description": "Cybersecurity fundamentals: network security, penetration testing, and ethical hacking.",
        "what_you_learn": ["Network Security", "Penetration Testing", "OWASP Top 10", "Cryptography", "Incident Response"],
    },
}

# Fallback for unknown skills
DEFAULT_RESOURCE = {
    "video_id": "rfscVS0vtbw",
    "title": "Programming Fundamentals — Full Course",
    "channel": "freeCodeCamp.org",
    "duration": "4 hours",
    "description": "Core programming concepts applicable to any language or domain.",
    "what_you_learn": ["Problem Solving", "Algorithms", "Data Structures", "Code Quality", "Debugging"],
}


def get_resource_for_skill(skill: str) -> dict:
    """Return the learning resource for a given skill, with video embed URL."""
    resource = LEARNING_RESOURCES.get(skill, DEFAULT_RESOURCE).copy()
    vid_id = resource.get("video_id", "rfscVS0vtbw")
    resource["embed_url"] = f"https://www.youtube-nocookie.com/embed/{vid_id}?rel=0&modestbranding=1"
    resource["youtube_url"] = f"https://www.youtube.com/watch?v={vid_id}"
    resource["skill"] = skill
    return resource


def get_learning_path(skills: list, weak_skills: list = None) -> list:
    """
    Build ordered learning path modules for a student.
    Prioritizes weak skills, then remaining skills.
    Returns list of resource dicts with index and status.
    """
    # Prioritize weak skills first
    ordered = []
    if weak_skills:
        for s in weak_skills:
            if s in skills and s not in ordered:
                ordered.append(s)
    for s in skills:
        if s not in ordered:
            ordered.append(s)

    # Cap at 5 modules
    modules = []
    for i, skill in enumerate(ordered[:5]):
        resource = get_resource_for_skill(skill)
        resource["module_index"] = i
        resource["module_number"] = i + 1
        modules.append(resource)

    return modules


def check_skill_in_opportunities(skills: list, title: str, description: str,
                                  tags: list, company: str = "") -> tuple:
    """
    Return (is_match: bool, match_score: float, matched_skills: list).
    Used to filter/rank opportunities by student skills.
    """
    if not skills:
        return True, 0.5, []

    text_lower = f"{title} {description} {company} {' '.join(tags)}".lower()
    matched = []
    for skill in skills:
        skill_low = skill.lower()
        # Check direct match and common abbreviations
        variants = [skill_low, skill_low.replace(".", ""), skill_low.replace("/", " ")]
        if any(v in text_lower for v in variants):
            matched.append(skill)

    if not matched:
        return False, 0.0, []

    match_score = len(matched) / len(skills)
    return True, match_score, matched
