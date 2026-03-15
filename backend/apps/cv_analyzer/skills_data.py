"""
Centralised skills database and job-category seed data for CV Analyzer.
200+ skills grouped by category.
"""

SKILLS_DATABASE: dict[str, list[str]] = {
    "programming_languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#",
        "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "R", "MATLAB",
        "Scala", "Perl", "Haskell", "Lua", "Dart", "Julia", "Groovy",
        "Elixir", "Clojure",
    ],
    "frameworks": [
        "Django", "FastAPI", "Flask", "React", "Vue.js", "Angular",
        "Next.js", "Nuxt.js", "Svelte", "Node.js", "Express.js",
        "Spring Boot", "Laravel", "Rails", "ASP.NET", "NestJS",
        "Gin", "Echo", "Fiber", "Actix", "Phoenix",
    ],
    "databases": [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
        "Oracle", "SQL Server", "Cassandra", "DynamoDB", "Firebase",
        "Elasticsearch", "InfluxDB", "Neo4j", "CouchDB", "MariaDB",
    ],
    "cloud": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Ansible", "Jenkins", "GitHub Actions", "GitLab CI",
        "CircleCI", "Helm", "Prometheus", "Grafana", "Heroku",
        "Nginx", "Apache",
    ],
    "data_science": [
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "scikit-learn", "Pandas", "NumPy", "Matplotlib", "Seaborn",
        "NLP", "Computer Vision", "spaCy", "NLTK", "Hugging Face",
        "Keras", "OpenCV", "Spark", "Hadoop", "Airflow", "MLflow",
        "Jupyter", "Tableau", "Power BI",
    ],
    "tools": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Linux", "Bash",
        "PowerShell", "REST API", "GraphQL", "gRPC", "Microservices",
        "Agile", "Scrum", "Kanban", "JIRA", "Confluence", "Postman",
        "Swagger", "CI/CD", "webpack", "Vite",
    ],
    "mobile": [
        "React Native", "Flutter", "Android", "iOS", "Xamarin",
        "Ionic", "Capacitor", "Expo",
    ],
    "security": [
        "Cybersecurity", "OWASP", "Penetration Testing", "Network Security",
        "Cryptography", "OAuth", "JWT", "SSL/TLS", "SIEM", "Firewall",
    ],
    "testing": [
        "Unit Testing", "Integration Testing", "Selenium", "Jest",
        "PyTest", "Cypress", "JMeter", "TestNG", "Mocha", "Chai",
    ],
    "design": [
        "Figma", "Adobe XD", "Sketch", "UI/UX Design", "Wireframing",
        "Prototyping", "User Research", "Photoshop", "Illustrator",
    ],
    "soft_skills": [
        "Leadership", "Communication", "Problem Solving", "Teamwork",
        "Project Management", "Critical Thinking", "Time Management",
        "Presentation", "Negotiation", "Mentoring",
    ],
}

# Seed data for JobCategory model (10 categories, 15-20 skills each)
JOB_CATEGORIES_SEED: list[dict] = [
    {
        "name": "Backend Developer",
        "slug": "backend-developer",
        "description": "Builds server-side logic, APIs and database integrations.",
        "required_skills": [
            "Python", "Django", "FastAPI", "MySQL", "PostgreSQL",
            "Redis", "Docker", "REST API", "Git", "Linux",
            "Celery", "JWT", "Unit Testing", "CI/CD", "AWS",
        ],
    },
    {
        "name": "Frontend Developer",
        "slug": "frontend-developer",
        "description": "Creates responsive user interfaces and client-side applications.",
        "required_skills": [
            "JavaScript", "TypeScript", "React", "Next.js", "HTML5",
            "CSS3", "Tailwind CSS", "Redux", "GraphQL", "Git",
            "Vite", "webpack", "Jest", "Figma", "REST API",
        ],
    },
    {
        "name": "Full Stack Developer",
        "slug": "full-stack-developer",
        "description": "Handles both frontend and backend development.",
        "required_skills": [
            "JavaScript", "TypeScript", "React", "Node.js", "Python",
            "Django", "MySQL", "PostgreSQL", "Docker", "Git",
            "REST API", "GraphQL", "Redis", "AWS", "CI/CD",
            "Unit Testing", "Linux",
        ],
    },
    {
        "name": "Data Scientist",
        "slug": "data-scientist",
        "description": "Analyses data and builds predictive models.",
        "required_skills": [
            "Python", "Pandas", "NumPy", "scikit-learn", "Jupyter",
            "Machine Learning", "TensorFlow", "PyTorch", "Matplotlib",
            "Seaborn", "SQL Server", "Git", "Tableau", "Spark",
            "Statistics",
        ],
    },
    {
        "name": "ML Engineer",
        "slug": "ml-engineer",
        "description": "Develops and deploys machine learning systems at scale.",
        "required_skills": [
            "Python", "TensorFlow", "PyTorch", "scikit-learn", "MLflow",
            "Docker", "Kubernetes", "Airflow", "Spark", "Git",
            "REST API", "AWS", "Hugging Face", "NLP", "Computer Vision",
        ],
    },
    {
        "name": "DevOps Engineer",
        "slug": "devops-engineer",
        "description": "Manages infrastructure, CI/CD pipelines and cloud operations.",
        "required_skills": [
            "Docker", "Kubernetes", "Terraform", "Ansible", "AWS",
            "Azure", "Linux", "Bash", "Jenkins", "GitHub Actions",
            "Prometheus", "Grafana", "Helm", "Git", "Python",
            "CI/CD", "Nginx",
        ],
    },
    {
        "name": "Mobile Developer",
        "slug": "mobile-developer",
        "description": "Builds native and cross-platform mobile applications.",
        "required_skills": [
            "React Native", "Flutter", "JavaScript", "TypeScript", "Swift",
            "Kotlin", "Android", "iOS", "Firebase", "REST API",
            "Git", "Expo", "Redux", "Unit Testing",
        ],
    },
    {
        "name": "UI/UX Designer",
        "slug": "ui-ux-designer",
        "description": "Designs intuitive user interfaces and experiences.",
        "required_skills": [
            "Figma", "Adobe XD", "Sketch", "UI/UX Design", "Wireframing",
            "Prototyping", "User Research", "Photoshop", "Illustrator",
            "HTML5", "CSS3", "Communication", "Presentation",
        ],
    },
    {
        "name": "Product Manager",
        "slug": "product-manager",
        "description": "Defines product vision and drives cross-functional execution.",
        "required_skills": [
            "Agile", "Scrum", "JIRA", "Confluence", "Project Management",
            "Communication", "Leadership", "Critical Thinking", "Presentation",
            "User Research", "Negotiation", "Tableau", "SQL Server", "Figma",
            "Roadmapping",
        ],
    },
    {
        "name": "Cybersecurity Engineer",
        "slug": "cybersecurity-engineer",
        "description": "Protects systems and data from cyber threats.",
        "required_skills": [
            "Cybersecurity", "OWASP", "Penetration Testing", "Network Security",
            "Cryptography", "Linux", "Bash", "Python", "Firewall",
            "SIEM", "OAuth", "JWT", "SSL/TLS", "Git", "Docker",
        ],
    },
]
