"""
Seed database with demo users and 35+ curated real opportunities.
Run: python seed_data.py
"""
import hashlib, json, sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from database import init_db, get_db, insert_opportunity, create_user

# Current reference date: April 2026
NOW = datetime(2026, 4, 15)

def dt(days_from_now):
    return (NOW + timedelta(days=days_from_now)).strftime("%Y-%m-%d")

def make_hash(title, source):
    return hashlib.sha256(f"{title.lower().strip()}::{source.lower()}".encode()).hexdigest()[:32]

DEMO_USERS = [
    {"email": "student@pulse.ai",   "password": "Demo@123", "name": "Arjun Sharma",     "role": "student",    "org": ""},
    {"email": "organizer@pulse.ai", "password": "Demo@123", "name": "TechFest 2026",    "role": "organizer",  "org": "IIIT Hyderabad"},
    {"email": "recruiter@pulse.ai", "password": "Demo@123", "name": "Priya Mehta (HR)", "role": "recruiter",  "org": "Google India"},
    {"email": "admin@pulse.ai",     "password": "PulseAdmin#2026X", "name": "System Admin", "role": "admin", "org": ""},
]

STUDENT_PROFILE = {
    "year": "3rd Year", "branch": "CSE", "college": "IIIT Hyderabad",
    "interests": ["AI/ML", "Web Development", "Data Science"],
    "preferred_categories": ["hackathon", "internship"],
    "location": "Hyderabad", "skills": ["Python", "React", "TensorFlow"],
    "linkedin": "https://linkedin.com/in/arjun-demo", "github": "https://github.com/arjun-demo"
}

SEED_OPPORTUNITIES = [
    # ── Hackathons ──────────────────────────────────────────────────────────────
    {
        "title": "Smart India Hackathon 2026",
        "category": "hackathon", "source": "sih.gov.in",
        "source_url": "https://www.sih.ac.in/",
        "apply_link": "https://www.sih.ac.in/",
        "deadline": dt(18), "reward": "₹1,00,000 Cash Prize",
        "reward_type": "cash", "prize_amount": 100000,
        "eligibility": "All UG/PG Students across India",
        "tags": ["AI/ML", "Govt", "Team Event", "All Branches"],
        "description": "India's largest student hackathon organized by Ministry of Education. Teams of 6 solve real government problem statements across 7 sectors. Grand prize ₹1 Lakh per winning team.",
        "company": "Ministry of Education, Govt. of India", "location": "Pan India",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "Google Solution Challenge 2026",
        "category": "hackathon", "source": "Google GDSC",
        "source_url": "https://developers.google.com/community/gdsc-solution-challenge",
        "apply_link": "https://developers.google.com/community/gdsc-solution-challenge",
        "deadline": dt(30), "reward": "$15,000 USD + Google Mentorship",
        "reward_type": "cash", "prize_amount": 1250000,
        "eligibility": "GDSC Members, 18-22 yrs",
        "tags": ["Google", "UN SDGs", "Android", "Web Dev", "Global"],
        "description": "Build solutions that address the UN's Sustainable Development Goals using Google technologies. Top 3 global winners get $15,000. Open to all GDSC members worldwide.",
        "company": "Google", "location": "Remote/Global",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "Microsoft Imagine Cup 2026",
        "category": "hackathon", "source": "Microsoft",
        "source_url": "https://imaginecup.microsoft.com/",
        "apply_link": "https://imaginecup.microsoft.com/",
        "deadline": dt(45), "reward": "$100,000 USD + Azure Credits",
        "reward_type": "cash", "prize_amount": 8300000,
        "eligibility": "Enrolled students under 30",
        "tags": ["Microsoft", "Azure", "AI", "Global Champion"],
        "description": "Microsoft's premier student technology competition. Build an AI-powered app that changes the world. Grand prize $100,000. Multi-round global competition with mentorship from Microsoft executives.",
        "company": "Microsoft", "location": "Remote/Global",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "Flipkart Grid 5.0 – E-Commerce Challenge",
        "category": "hackathon", "source": "Unstop",
        "source_url": "https://unstop.com/hackathons/flipkart-grid-50",
        "apply_link": "https://unstop.com/hackathons/flipkart-grid-50",
        "deadline": dt(5), "reward": "₹5,00,000 + PPO at Flipkart",
        "reward_type": "cash", "prize_amount": 500000,
        "eligibility": "Pre-final year CSE/IT/ECE students",
        "tags": ["Flipkart", "E-Commerce", "CSE", "PPO", "Closing Soon"],
        "description": "Flipkart's flagship engineering challenge tests problem-solving through Quiz + Coding + Innovation rounds. Winners get ₹5 Lakhs and a Pre-Placement Offer at Flipkart.",
        "company": "Flipkart", "location": "Remote + Bengaluru Finals",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "HackWithInfy – Infosys Hackathon",
        "category": "hackathon", "source": "Infosys",
        "source_url": "https://www.infosys.com/careers/hackwithInfy.html",
        "apply_link": "https://www.infosys.com/careers/hackwithInfy.html",
        "deadline": dt(25), "reward": "₹1,25,000 + Infosys Internship",
        "reward_type": "cash", "prize_amount": 125000,
        "eligibility": "3rd & 4th Year B.Tech/B.E.",
        "tags": ["Infosys", "CSE", "Internship Offer", "2026 Batch"],
        "description": "Infosys' annual hackathon for engineering students. Solve open innovation challenges using cutting-edge tech. Winners get cash prizes and a fast-track to Infosys internship/placement.",
        "company": "Infosys", "location": "Remote",
        "status": "approved",
    },
    {
        "title": "Devfolio Build For Bharat Hackathon",
        "category": "hackathon", "source": "Devfolio",
        "source_url": "https://devfolio.co/",
        "apply_link": "https://devfolio.co/",
        "deadline": dt(12), "reward": "₹2,00,000 + VC Meetings",
        "reward_type": "cash", "prize_amount": 200000,
        "eligibility": "Open to All Students",
        "tags": ["Web3", "Social Impact", "India Stack", "Open Source"],
        "description": "Build tech solutions for India's unique challenges. Powered by Devfolio, top submissions get VC funding meetings, mentorship, and ₹2 Lakhs cash pool split across categories.",
        "company": "Devfolio", "location": "Remote",
        "status": "approved",
    },
    {
        "title": "MLH Global Hack Week – AI Edition",
        "category": "hackathon", "source": "MLH",
        "source_url": "https://mlh.io/",
        "apply_link": "https://mlh.io/",
        "deadline": dt(8), "reward": "MLH Swag + Certificate",
        "reward_type": "certificate", "prize_amount": 0,
        "eligibility": "Students 18+",
        "tags": ["MLH", "AI/ML", "Beginner Friendly", "Global"],
        "description": "Major League Hacking's signature weekly event series. Learn, build, and ship AI projects in 7 days. Every participant gets verified MLH certificate + exclusive swag kit.",
        "company": "Major League Hacking", "location": "Remote/Global",
        "status": "approved",
    },
    {
        "title": "NASSCOM Technovation Challenge",
        "category": "hackathon", "source": "NASSCOM",
        "source_url": "https://nasscom.in/",
        "apply_link": "https://nasscom.in/technovation",
        "deadline": dt(35), "reward": "₹3,00,000 + NASSCOM Membership",
        "reward_type": "cash", "prize_amount": 300000,
        "eligibility": "UG/PG students from recognized institutions",
        "tags": ["NASSCOM", "IT Policy", "Startup", "National Level"],
        "description": "India's premier technology industry body challenges students to solve IT policy and innovation problems. Winners receive ₹3 Lakhs and a 1-year NASSCOM membership for startup support.",
        "company": "NASSCOM", "location": "Hybrid (Delhi NCR)",
        "status": "approved",
    },
    # ── Internships ─────────────────────────────────────────────────────────────
    {
        "title": "Google STEP Intern 2026 – Software Engineering",
        "category": "internship", "source": "Google Careers",
        "source_url": "https://careers.google.com/students/",
        "apply_link": "https://careers.google.com/students/",
        "deadline": dt(20), "reward": "₹1,20,000/month Stipend",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "1st & 2nd Year B.Tech/B.E. (CSE/IT)",
        "tags": ["Google", "SDE", "FAANG", "1st Year", "2nd Year"],
        "description": "Google's Student Training in Engineering Program (STEP) is a 12-week summer internship for freshman and sophomore students. Full stipend + housing allowance + return offer potential.",
        "company": "Google India", "location": "Hyderabad / Bengaluru",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "Microsoft Explore Internship – SDE",
        "category": "internship", "source": "Microsoft Careers",
        "source_url": "https://careers.microsoft.com/students/",
        "apply_link": "https://careers.microsoft.com/students/",
        "deadline": dt(28), "reward": "₹1,00,000/month Stipend",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "2nd Year B.Tech CSE/ECE/IT",
        "tags": ["Microsoft", "SDE", "FAANG", "Explorer", "Azure"],
        "description": "Microsoft's Explore internship gives sophomore students a 12-week engineering experience. Work on real Azure/Office/Windows products with dedicated mentors. Path to SWE full-time.",
        "company": "Microsoft India", "location": "Hyderabad / Noida",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "Flipkart SDE Intern – Platform Engineering",
        "category": "internship", "source": "Flipkart Careers",
        "source_url": "https://careers.flipkart.com/",
        "apply_link": "https://careers.flipkart.com/",
        "deadline": dt(15), "reward": "₹60,000/month Stipend + PPO",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "3rd Year B.Tech CSE/IT/ECE",
        "tags": ["Flipkart", "SDE", "E-Commerce", "PPO", "Bengaluru"],
        "description": "Join Flipkart's Platform Engineering team for a 6-month SDE internship. Build systems that serve 500M+ users. Pre-Placement Offer given to top performers. India's top e-commerce unicorn.",
        "company": "Flipkart", "location": "Bengaluru",
        "status": "approved",
    },
    {
        "title": "DRDO Summer Research Internship",
        "category": "internship", "source": "DRDO",
        "source_url": "https://www.drdo.gov.in/",
        "apply_link": "https://www.drdo.gov.in/internship",
        "deadline": dt(10), "reward": "₹6,000/month Stipend",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "3rd+ Year B.Tech/M.Tech (All Engineering Branches)",
        "tags": ["DRDO", "Govt", "Defence Tech", "Research", "Security Clearance"],
        "description": "DRDO's prestigious research internship program. Work at India's top defence research labs on aerospace, cybersecurity, electronics, and materials. Requires security clearance. Certificate + stipend.",
        "company": "DRDO (Govt. of India)", "location": "Delhi / Pune / Hyderabad",
        "status": "approved",
    },
    {
        "title": "ISRO Summer Internship Programme",
        "category": "internship", "source": "ISRO",
        "source_url": "https://www.isro.gov.in/",
        "apply_link": "https://www.isro.gov.in/capacity-building/internship",
        "deadline": dt(3), "reward": "₹8,000/month + ISRO Certificate",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "3rd+ Year B.Tech (CSE/ECE/ME/Aerospace)",
        "tags": ["ISRO", "Space", "Govt", "Aerospace", "Research", "Urgent"],
        "description": "Work at India's space agency on real satellite communication, onboard computer, and propulsion projects. One of the most prestigious internship programs for Indian engineering students.",
        "company": "Indian Space Research Organisation", "location": "Bengaluru / Thiruvananthapuram",
        "status": "approved",
    },
    {
        "title": "Internshala – Data Science Internship at Meesho",
        "category": "internship", "source": "Internshala",
        "source_url": "https://internshala.com/",
        "apply_link": "https://internshala.com/internship/detail/data-science-internship-meesho",
        "deadline": dt(22), "reward": "₹25,000/month Stipend",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "2nd/3rd Year (CSE/Math/Stats background)",
        "tags": ["Data Science", "Python", "ML", "Meesho", "Social Commerce"],
        "description": "3-month data science internship with Meesho's growth analytics team. Work on recommendation algorithms and supply chain forecasting models. Remote-friendly with flexible hours.",
        "company": "Meesho", "location": "Remote",
        "status": "approved",
    },
    {
        "title": "Morgan Stanley Technology Analyst Intern",
        "category": "internship", "source": "Morgan Stanley",
        "source_url": "https://www.morganstanley.com/careers/students-graduates",
        "apply_link": "https://www.morganstanley.com/careers/students-graduates",
        "deadline": dt(40), "reward": "₹80,000/month Stipend",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "3rd Year B.Tech CSE/IT with 8+ CGPA",
        "tags": ["Morgan Stanley", "Fintech", "CGPA 8+", "Finance", "Quant"],
        "description": "10-week summer technology internship at Morgan Stanley's Mumbai/Bengaluru tech centers. Build trading platforms, risk systems, and backend services for global financial products.",
        "company": "Morgan Stanley India", "location": "Mumbai / Bengaluru",
        "status": "approved",
    },
    # ── Scholarships ────────────────────────────────────────────────────────────
    {
        "title": "National Scholarship Portal – PM Scholarship 2026",
        "category": "scholarship", "source": "scholarships.gov.in",
        "source_url": "https://scholarships.gov.in/",
        "apply_link": "https://scholarships.gov.in/",
        "deadline": dt(60), "reward": "₹12,000/year (Girls) | ₹10,000/year (Boys)",
        "reward_type": "cash", "prize_amount": 12000,
        "eligibility": "All UG students from low-income families (income < ₹2.5L/yr)",
        "tags": ["Govt", "NSP", "All Branches", "Income Based", "Annual Renewable"],
        "description": "India's flagship national scholarship portal offering 5000+ schemes. Apply once, benefit from multiple central and state scholarships. Direct bank transfer. Income-based eligibility.",
        "company": "Ministry of Education, Govt. of India", "location": "Pan India",
        "status": "approved", "is_featured": 1,
    },
    {
        "title": "Reliance Foundation UG Scholarship 2026",
        "category": "scholarship", "source": "reliancefoundation.org",
        "source_url": "https://reliancefoundation.org/scholarships",
        "apply_link": "https://reliancefoundation.org/scholarships",
        "deadline": dt(35), "reward": "₹2,00,000 (one-time) + Mentorship",
        "reward_type": "cash", "prize_amount": 200000,
        "eligibility": "1st Year UG students, merit-cum-means",
        "tags": ["Reliance", "Merit-Cum-Means", "1st Year", "STEM", "Arts & Commerce"],
        "description": "Reliance Foundation's scholarship for 5,000 meritorious undergraduate students per year. Covers tuition + living expenses up to ₹2 Lakhs. Includes mentorship by Reliance professionals.",
        "company": "Reliance Foundation", "location": "Pan India",
        "status": "approved",
    },
    {
        "title": "Sitaram Jindal Foundation Scholarship",
        "category": "scholarship", "source": "sitaramjindalfoundation.org",
        "source_url": "https://www.sitaramjindalfoundation.org/",
        "apply_link": "https://www.sitaramjindalfoundation.org/scholarship",
        "deadline": dt(50), "reward": "₹3,500/month for UG students",
        "reward_type": "cash", "prize_amount": 42000,
        "eligibility": "Meritorious students with family income < ₹2L/yr",
        "tags": ["Jindal", "Monthly Stipend", "All Branches", "Private"],
        "description": "Monthly stipend of ₹3,500 for UG engineering students throughout the degree duration. One of the most accessible scholarships for meritorious students from economically weaker sections.",
        "company": "Sitaram Jindal Foundation", "location": "Pan India",
        "status": "approved",
    },
    {
        "title": "HDFC Badhte Kadam – Education Scholarship",
        "category": "scholarship", "source": "hdfcbank.com",
        "source_url": "https://www.hdfcbank.com/content/bbp/repositories/723fb80a",
        "apply_link": "https://www.hdfcbank.com/",
        "deadline": dt(42), "reward": "₹75,000 (one-time)",
        "reward_type": "cash", "prize_amount": 75000,
        "eligibility": "Meritorious students in financial need, family income < ₹5L",
        "tags": ["HDFC", "Banking", "Merit-Cum-Means", "10% Family Income"],
        "description": "HDFC Bank's CSR scholarship program for financially needy meritorious students. One-time award of ₹75,000 paid directly to institution. Simple online application process.",
        "company": "HDFC Bank CSR", "location": "Pan India",
        "status": "approved",
    },
    {
        "title": "AICTE – Pragati Scholarship for Girls",
        "category": "scholarship", "source": "AICTE",
        "source_url": "https://www.aicte-india.org/bureaus/pgov91/AICTE_Scholarship",
        "apply_link": "https://www.aicte-india.org/",
        "deadline": dt(55), "reward": "₹50,000/year + Tuition Fee Reimbursement",
        "reward_type": "cash", "prize_amount": 50000,
        "eligibility": "Female students in AICTE-approved colleges, income < ₹8L",
        "tags": ["AICTE", "Women in STEM", "Govt", "Annual", "All Technical Branches"],
        "description": "AICTE Pragati Scholarship provides financial support exclusively to girl students pursuing technical education. Covers tuition fees up to ₹30,000 + ₹20,000 incidental charges per year.",
        "company": "AICTE, Govt. of India", "location": "Pan India",
        "status": "approved",
    },
    # ── Workshops / Upskilling ──────────────────────────────────────────────────
    {
        "title": "Google Cloud – Machine Learning Crash Course (Free)",
        "category": "workshop", "source": "Google",
        "source_url": "https://developers.google.com/machine-learning/crash-course",
        "apply_link": "https://developers.google.com/machine-learning/crash-course",
        "deadline": None, "reward": "Google Certificate (Verified)",
        "reward_type": "certificate", "prize_amount": 0,
        "eligibility": "Open to All",
        "tags": ["Google", "ML", "Free", "Self-paced", "Certificate", "Beginner"],
        "description": "Google's free 15-hour Machine Learning Crash Course created by Google engineers. Learn TensorFlow basics, neural networks, ML concepts with interactive exercises and real-world case studies.",
        "company": "Google Developers", "location": "Online (Self-paced)",
        "status": "approved",
    },
    {
        "title": "AWS Cloud Practitioner – Free Training Week",
        "category": "workshop", "source": "AWS",
        "source_url": "https://aws.amazon.com/training/awsacademy/",
        "apply_link": "https://aws.amazon.com/training/awsacademy/",
        "deadline": dt(14), "reward": "AWS Academy Certificate + Free Exam Voucher",
        "reward_type": "certificate", "prize_amount": 0,
        "eligibility": "Students enrolled in AWS Academy institutions",
        "tags": ["AWS", "Cloud", "DevOps", "Free Exam Voucher", "Certification Prep"],
        "description": "AWS Academy's intensive free training week for cloud fundamentals. Includes 40 hours of content, hands-on labs, and a free AWS Certified Cloud Practitioner exam voucher (worth ₹8,000).",
        "company": "Amazon Web Services", "location": "Online",
        "status": "approved",
    },
    {
        "title": "NVIDIA Deep Learning Institute – Free Workshop",
        "category": "workshop", "source": "NVIDIA DLI",
        "source_url": "https://www.nvidia.com/en-us/training/",
        "apply_link": "https://www.nvidia.com/en-us/training/",
        "deadline": dt(20), "reward": "NVIDIA DLI Certificate",
        "reward_type": "certificate", "prize_amount": 0,
        "eligibility": "Students with basic Python knowledge",
        "tags": ["NVIDIA", "Deep Learning", "GPU", "PyTorch", "Free", "Certificate"],
        "description": "NVIDIA's Deep Learning Institute offering free workshop on 'Fundamentals of Deep Learning'. Hands-on GPU-accelerated training in PyTorch. Earn a globally recognized NVIDIA DLI certificate.",
        "company": "NVIDIA DLI", "location": "Online",
        "status": "approved",
    },
    {
        "title": "GitHub Campus Expert Bootcamp 2026",
        "category": "workshop", "source": "GitHub",
        "source_url": "https://education.github.com/experts",
        "apply_link": "https://education.github.com/experts",
        "deadline": dt(28), "reward": "GitHub Campus Expert Badge + Swag + $200 Credits",
        "reward_type": "free", "prize_amount": 0,
        "eligibility": "Students 18+ with active student community involvement",
        "tags": ["GitHub", "Open Source", "Leadership", "Developer Advocacy", "Swag"],
        "description": "Apply to become a GitHub Campus Expert. 4-week online bootcamp covering open source, technical writing, and community building. Graduates get GitHub Pro, exclusive swag, and $200 in GitHub credits.",
        "company": "GitHub Education", "location": "Online",
        "status": "approved",
    },
    {
        "title": "Cisco NetAcad – Cybersecurity Essentials (Free)",
        "category": "workshop", "source": "Cisco NetAcad",
        "source_url": "https://www.netacad.com/",
        "apply_link": "https://www.netacad.com/",
        "deadline": None, "reward": "Cisco NetAcad Badge + Digital Certificate",
        "reward_type": "certificate", "prize_amount": 0,
        "eligibility": "Open to All",
        "tags": ["Cisco", "Cybersecurity", "Networking", "Free", "Self-paced", "CCNA Prep"],
        "description": "Complete free cybersecurity foundations course by Cisco Networking Academy. 30 hours of content covering networking basics, ethical hacking concepts, and digital defense strategies.",
        "company": "Cisco Networking Academy", "location": "Online (Self-paced)",
        "status": "approved",
    },
    {
        "title": "Microsoft AI Skills Challenge – April 2026",
        "category": "workshop", "source": "Microsoft Learn",
        "source_url": "https://developer.microsoft.com/en-us/offers/ai-skills-challenge",
        "apply_link": "https://developer.microsoft.com/en-us/offers/ai-skills-challenge",
        "deadline": dt(16), "reward": "Free Azure AI-900 Exam Voucher (₹6,000 value)",
        "reward_type": "certificate", "prize_amount": 0,
        "eligibility": "Open to All Students",
        "tags": ["Microsoft", "Azure", "AI", "Free Exam Voucher", "GPT", "Copilot"],
        "description": "Complete Microsoft's April AI Skills Challenge and earn a free voucher for the Azure AI Fundamentals exam (AI-900). Learn about Azure OpenAI, Copilot, and responsible AI principles.",
        "company": "Microsoft", "location": "Online",
        "status": "approved",
    },
    # ── Jobs (Entry Level) ──────────────────────────────────────────────────────
    {
        "title": "Amazon – Graduate SDE (2026 Batch)",
        "category": "job", "source": "Amazon Jobs",
        "source_url": "https://www.amazon.jobs/en/business_categories/student-programs",
        "apply_link": "https://www.amazon.jobs/",
        "deadline": dt(30), "reward": "₹45–55 LPA CTC",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "2026 graduating batch, CSE/IT/ECE, CGPA 7+",
        "tags": ["Amazon", "FAANG", "SDE", "2026 Batch", "Freshers"],
        "description": "Amazon's campus hiring for 2026 graduating batch. Full-time Software Development Engineer roles across AWS, Alexa, and Amazon.in teams. DSA + System Design interview process.",
        "company": "Amazon India", "location": "Hyderabad / Bengaluru / Chennai",
        "status": "approved",
    },
    {
        "title": "Zomato – Product Graduate (2026 Batch)",
        "category": "job", "source": "Zomato Careers",
        "source_url": "https://www.zomato.com/careers",
        "apply_link": "https://www.zomato.com/careers",
        "deadline": dt(20), "reward": "₹20–30 LPA CTC",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "2026 batch, Any branch, strong analytical skills",
        "tags": ["Zomato", "Product", "Startup", "Freshers", "2026 Batch"],
        "description": "Zomato is hiring Product & Engineering graduates (2026 batch) to build features used by 100M+ users. Strong analytical thinking and product sense required. Fast-paced startup culture.",
        "company": "Zomato", "location": "Gurugram",
        "status": "approved",
    },
    {
        "title": "Juspay – Frontend Engineer (Fresher)",
        "category": "job", "source": "Juspay Careers",
        "source_url": "https://juspay.in/",
        "apply_link": "https://juspay.in/careers",
        "deadline": dt(18), "reward": "₹18–24 LPA CTC",
        "reward_type": "stipend", "prize_amount": 0,
        "eligibility": "Freshers 2025/2026 batch, strong JavaScript",
        "tags": ["Juspay", "Fintech", "Frontend", "React", "2026 Batch", "Startup"],
        "description": "Juspay (India's leading payment orchestration platform) hiring frontend engineers. Work on checkout flows used by 50M+ transactions/day. Functional programming with PureScript/ReasonML.",
        "company": "Juspay", "location": "Bengaluru",
        "status": "approved",
    },
]


def _print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode())

def seed():
    _print("Initializing database...")
    init_db()

    conn = get_db()
    _print("Creating demo users...")
    for u in DEMO_USERS:
        ph = generate_password_hash(u["password"])
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (email, password_hash, name, role, organization) VALUES (?,?,?,?,?)",
                (u["email"], ph, u["name"], u["role"], u["org"]),
            )
        except Exception as e:
            _print(f"   Skipping {u['email']}: {e}")

    # Set student profile
    student = conn.execute("SELECT id FROM users WHERE email='student@pulse.ai'").fetchone()
    if student:
        conn.execute("UPDATE users SET profile=? WHERE id=?", (json.dumps(STUDENT_PROFILE), student["id"]))

    conn.commit()

    _print("Seeding opportunities...")
    new_count = 0
    for opp in SEED_OPPORTUNITIES:
        opp["hash"] = make_hash(opp["title"], opp["source"])
        _, is_new = insert_opportunity(opp)
        if is_new:
            new_count += 1

    conn.close()
    _print(f"Done! Added {new_count}/{len(SEED_OPPORTUNITIES)} opportunities.")
    _print("\nDemo Login Credentials:")
    _print("  Student:   student@pulse.ai    / Demo@123")
    _print("  Organizer: organizer@pulse.ai  / Demo@123")
    _print("  Recruiter: recruiter@pulse.ai  / Demo@123")
    _print("  Admin URL: /pulse-command-x9")
    _print("  Admin:     admin@pulse.ai      / PulseAdmin#2026X")


if __name__ == "__main__":
    seed()
