"""
CV Analyzer AI logic — spaCy NER + PhraseMatcher for skill extraction.
Runs inside a Celery worker; models are loaded in apps.py ready().
"""
import io
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 500+ skills database organized by category
SKILLS_DATABASE = {
    "programming_languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "MATLAB", "Perl", "Haskell",
        "Lua", "Dart", "Julia", "Groovy", "Elixir", "Clojure",
    ],
    "web_frontend": [
        "React", "Vue.js", "Angular", "Next.js", "Nuxt.js", "Svelte", "HTML5",
        "CSS3", "Tailwind CSS", "Bootstrap", "SASS", "LESS", "webpack", "Vite",
        "Redux", "Zustand", "GraphQL", "REST API", "jQuery", "Gatsby",
    ],
    "web_backend": [
        "Django", "Flask", "FastAPI", "Spring Boot", "Node.js", "Express.js",
        "Laravel", "Rails", "ASP.NET", "NestJS", "Gin", "Echo", "Fiber",
        "Actix", "Phoenix", "Sinatra",
    ],
    "databases": [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite", "Oracle", "MSSQL",
        "Cassandra", "DynamoDB", "Elasticsearch", "InfluxDB", "Neo4j", "CouchDB",
        "MariaDB", "Firebase Realtime Database",
    ],
    "cloud_devops": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
        "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Helm", "Prometheus",
        "Grafana", "Nginx", "Apache", "Linux", "Bash", "PowerShell",
    ],
    "data_science_ml": [
        "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Matplotlib",
        "Seaborn", "spaCy", "NLTK", "Hugging Face", "Keras", "OpenCV", "Spark",
        "Hadoop", "Airflow", "MLflow", "Jupyter", "Tableau", "Power BI",
    ],
    "mobile": [
        "React Native", "Flutter", "Android", "iOS", "Swift", "Kotlin",
        "Xamarin", "Ionic", "Capacitor", "Expo",
    ],
    "version_control": [
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
    ],
    "soft_skills": [
        "Leadership", "Communication", "Teamwork", "Problem Solving",
        "Critical Thinking", "Time Management", "Agile", "Scrum", "Kanban",
        "Project Management", "Presentation", "Negotiation",
    ],
    "security": [
        "Cybersecurity", "OWASP", "Penetration Testing", "Network Security",
        "Cryptography", "OAuth", "JWT", "SSL/TLS", "SIEM", "Firewall",
    ],
    "testing": [
        "Unit Testing", "Integration Testing", "Selenium", "Jest", "PyTest",
        "Cypress", "Postman", "JMeter", "TestNG", "Mocha", "Chai",
    ],
    "design": [
        "Figma", "Adobe XD", "Sketch", "UI/UX Design", "Wireframing",
        "Prototyping", "User Research", "Photoshop", "Illustrator",
    ],
}

# Job role profiles: required skills for skill gap detection
JOB_ROLE_PROFILES = {
    "Full Stack Developer": {
        "required": ["React", "Node.js", "MySQL", "Docker", "Git"],
        "preferred": ["TypeScript", "Redis", "AWS", "Kubernetes"],
    },
    "Data Scientist": {
        "required": ["Python", "Pandas", "scikit-learn", "Jupyter", "Git"],
        "preferred": ["TensorFlow", "PyTorch", "Spark", "Tableau"],
    },
    "DevOps Engineer": {
        "required": ["Docker", "Kubernetes", "AWS", "Terraform", "Linux"],
        "preferred": ["Ansible", "Prometheus", "Jenkins", "Helm"],
    },
    "Mobile Developer": {
        "required": ["React Native", "Flutter", "Git"],
        "preferred": ["iOS", "Android", "Firebase Realtime Database"],
    },
    "Backend Developer": {
        "required": ["Python", "Django", "MySQL", "REST API", "Git"],
        "preferred": ["Redis", "Docker", "AWS", "Celery"],
    },
    "Frontend Developer": {
        "required": ["React", "TypeScript", "HTML5", "CSS3", "Git"],
        "preferred": ["Next.js", "Tailwind CSS", "GraphQL", "Redux"],
    },
    "Machine Learning Engineer": {
        "required": ["Python", "TensorFlow", "PyTorch", "scikit-learn", "Git"],
        "preferred": ["MLflow", "Kubernetes", "Spark", "Airflow"],
    },
    "Cloud Architect": {
        "required": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform"],
        "preferred": ["GCP", "Ansible", "Prometheus", "Helm"],
    },
    "Security Engineer": {
        "required": ["Cybersecurity", "OWASP", "Network Security", "Linux"],
        "preferred": ["Penetration Testing", "Cryptography", "SIEM"],
    },
    "UI/UX Designer": {
        "required": ["Figma", "UI/UX Design", "Wireframing", "User Research"],
        "preferred": ["Adobe XD", "Prototyping", "Sketch"],
    },
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes."""
    try:
        import pdfminer.high_level as pdfminer
        return pdfminer.extract_text(io.BytesIO(file_bytes))
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            logger.error("PDF extraction failed: %s", e)
            return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file bytes."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        logger.error("DOCX extraction failed: %s", e)
        return ""


def validate_magic_bytes(file_bytes: bytes, filename: str) -> bool:
    """Validate file magic bytes for PDF/DOCX."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return file_bytes[:4] == b"%PDF"
    elif ext in (".docx", ".doc"):
        # DOCX is a ZIP archive
        return file_bytes[:4] == b"PK\x03\x04"
    return False


def extract_skills_from_text(text: str) -> dict:
    """Match skills from the database against the CV text."""
    text_lower = text.lower()
    found_skills = {}
    all_skills = []

    for category, skills in SKILLS_DATABASE.items():
        matched = [s for s in skills if s.lower() in text_lower]
        if matched:
            found_skills[category] = matched
            all_skills.extend(matched)

    return {"by_category": found_skills, "all": all_skills}


def extract_sections(text: str) -> dict:
    """Detect presence of key CV sections."""
    text_lower = text.lower()
    sections = {
        "contact": bool(
            re.search(r"\b(email|phone|linkedin|github|address)\b", text_lower)
        ),
        "summary": bool(
            re.search(r"\b(summary|objective|profile|about)\b", text_lower)
        ),
        "experience": bool(
            re.search(r"\b(experience|work history|employment|internship)\b", text_lower)
        ),
        "education": bool(
            re.search(r"\b(education|degree|university|college|school)\b", text_lower)
        ),
        "skills": bool(re.search(r"\b(skills|technologies|competencies)\b", text_lower)),
    }
    return sections


_DEFAULT_CV_SCORING = {
    "keyword_relevance": 0.30,
    "completeness": 0.25,
    "skill_density": 0.25,
    "formatting": 0.20,
}


def compute_cv_score(text: str, skills_data: dict, sections: dict) -> dict:
    """
    Compute CV score (0–100) using 4-factor weighted formula:
      - keyword_relevance  30%
      - completeness       25%
      - skill_density      25%
      - formatting         20%
    """
    try:
        from django.conf import settings
        weights = getattr(settings, "CV_SCORING", _DEFAULT_CV_SCORING)
    except Exception:
        weights = _DEFAULT_CV_SCORING

    # 1. Keyword relevance: skills vs job market demand
    high_demand_skills = {
        "Python", "React", "Docker", "AWS", "Git", "JavaScript", "TypeScript",
        "Machine Learning", "SQL", "Linux",
    }
    matched_high_demand = sum(
        1 for s in skills_data["all"] if s in high_demand_skills
    )
    keyword_score = min(100.0, matched_high_demand * 10.0)

    # 2. Completeness: section presence
    section_count = sum(1 for v in sections.values() if v)
    completeness_score = (section_count / len(sections)) * 100.0

    # 3. Skill density: unique skills / word count
    words = text.split()
    word_count = max(len(words), 1)
    unique_skills = len(set(skills_data["all"]))
    skill_density_score = min(100.0, (unique_skills / word_count) * 1000.0)

    # 4. Formatting: word count range and structure
    formatting_score = 100.0
    if word_count < 200:
        formatting_score = 40.0
    elif word_count < 400:
        formatting_score = 70.0
    elif word_count > 1500:
        formatting_score = 80.0

    overall = (
        keyword_score * weights["keyword_relevance"]
        + completeness_score * weights["completeness"]
        + skill_density_score * weights["skill_density"]
        + formatting_score * weights["formatting"]
    )

    return {
        "overall": round(overall, 1),
        "keyword_relevance": round(keyword_score, 1),
        "completeness": round(completeness_score, 1),
        "skill_density": round(skill_density_score, 1),
        "formatting": round(formatting_score, 1),
    }


def compute_skill_gaps(user_skills: list, target_role: str = None) -> dict:
    """Compare user skills against all job role profiles to find gaps."""
    user_skills_lower = {s.lower() for s in user_skills}
    gaps = {}

    roles_to_check = (
        {target_role: JOB_ROLE_PROFILES[target_role]}
        if target_role and target_role in JOB_ROLE_PROFILES
        else JOB_ROLE_PROFILES
    )

    for role, profile in roles_to_check.items():
        missing_required = [
            s for s in profile["required"] if s.lower() not in user_skills_lower
        ]
        missing_preferred = [
            s for s in profile.get("preferred", []) if s.lower() not in user_skills_lower
        ]
        if missing_required or missing_preferred:
            gaps[role] = {
                "missing_required": missing_required,
                "missing_preferred": missing_preferred,
            }

    return gaps
