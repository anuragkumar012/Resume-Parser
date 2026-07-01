import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_resume_pdf(filepath: str, name: str, email: str, phone: str, location: str, sections: dict):
    """Creates a sample PDF resume using ReportLab."""
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Name', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=5
    )
    contact_style = ParagraphStyle(
        'Contact', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#4A5568"), spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'Section', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceBefore=10, spaceAfter=5
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor("#2D3748"), spaceAfter=5
    )
    
    story = []
    story.append(Paragraph(name, title_style))
    story.append(Paragraph(f"Email: {email} | Phone: {phone} | Location: {location}", contact_style))
    
    for section_title, content in sections.items():
        story.append(Paragraph(section_title, h2_style))
        story.append(Spacer(1, 2))
        
        # Split by newlines and add paragraphs
        for line in content.split('\n'):
            line_strip = line.strip()
            if line_strip:
                story.append(Paragraph(line_strip, body_style))
        story.append(Spacer(1, 8))
        
    doc.build(story)

def main():
    os.makedirs("samples", exist_ok=True)
    
    # 1. Alice Smith - Software Engineer
    alice_sections = {
        "Professional Summary": (
            "Senior Software Engineer with 6+ years of experience designing, building, and deploying highly scalable python applications. "
            "Expert in web backend architectures, RESTful APIs, and cloud deployments."
        ),
        "Skills": (
            "- Programming Languages: Python, JavaScript, SQL, Bash\n"
            "- Frameworks: Django, FastAPI, React, Node.js, Flask\n"
            "- Databases: PostgreSQL, MongoDB, Redis\n"
            "- Cloud & DevOps: AWS EC2, AWS S3, Docker, Kubernetes, Git, CI/CD"
        ),
        "Experience": (
            "Senior Python Developer | TechCorp LLC | June 2021 - Present\n"
            "- Spearheaded the redesign of a legacy monolithic service into FastAPI microservices, increasing throughput by 40%.\n"
            "- Architected real-time dashboard data streams using AWS EC2, AWS S3, and Redis caching.\n"
            "- Integrated third-party APIs and secured authentication with OAuth2/JWT.\n"
            "- Tech stack: Python, Django, FastAPI, AWS EC2, AWS S3, PostgreSQL, Redis, Git, Docker.\n\n"
            "Software Engineer | InnovateTech | January 2018 - May 2021\n"
            "- Developed responsive frontend user interfaces using React and state management.\n"
            "- Built REST APIs in Node.js and Django for high-traffic e-commerce systems.\n"
            "- Reduced build/deploy pipelines times by 25% by writing custom Dockerfiles and Github Action workflows.\n"
            "- Tech stack: React, Node.js, Python, Django, MongoDB, Docker, Git."
        ),
        "Projects": (
            "E-Commerce Microservices Engine\n"
            "- Designed transactional microservices using FastAPI, Redis, and PostgreSQL deployed on AWS.\n"
            "Real-Time Analysis Dashboard\n"
            "- Built a responsive dashboard using React and Django WebSocket connections."
        ),
        "Education": (
            "Bachelor of Science (B.Sc.) in Computer Science\n"
            "State University | 2014 - 2018 | CGPA: 3.8/4.0"
        ),
        "Certifications": (
            "- AWS Certified Solutions Architect - Associate (2022)\n"
            "- Certified Kubernetes Administrator (CKA) (2023)"
        )
    }
    create_resume_pdf(
        "samples/resume_alice_software_engineer.pdf",
        "Alice Smith",
        "alice.smith@example.com",
        "+1-555-0199",
        "New York, NY",
        alice_sections
    )
    
    # 2. Bob Jones - Data Scientist
    bob_sections = {
        "Summary": (
            "Passionate Data Scientist with 4 years of experience building predictive models, training machine learning algorithms, "
            "and extracting business insights from large unstructured datasets."
        ),
        "Skills": (
            "- Core Skills: Machine Learning, Data Analytics, Deep Learning, Natural Language Processing (NLP)\n"
            "- Programming: Python, R, SQL\n"
            "- Libraries: Scikit-Learn, PyTorch, TensorFlow, Pandas, NumPy, NLTK, SpaCy\n"
            "- Cloud & Databases: GCP, MongoDB, PostgreSQL, Tableau"
        ),
        "Experience": (
            "Data Scientist | DataInsights Inc. | August 2022 - Present\n"
            "- Developed and deployed an NLP classification model using SpaCy and Scikit-Learn that categorized customer feedback with 91% accuracy.\n"
            "- Built predictive regression models in PyTorch that forecast monthly sales, saving $50k in inventory overhead.\n"
            "- Designed analytics dashboards in Tableau linked with PostgreSQL backend.\n"
            "- Tech stack: Python, Scikit-Learn, PyTorch, Pandas, PostgreSQL, GCP.\n\n"
            "Junior Data Analyst | FinancialLogic | June 2020 - July 2022\n"
            "- Cleaned and preprocessed massive structured and unstructured datasets using Pandas and NumPy.\n"
            "- Performed A/B testing on search query layouts, increasing click-through rates by 8%.\n"
            "- Tech stack: Python, Pandas, NumPy, SQL, R."
        ),
        "Education": (
            "Master of Science (M.S.) in Data Science\n"
            "Tech Institute of Technology | 2018 - 2020\n\n"
            "Bachelor of Science (B.S.) in Mathematics\n"
            "State College | 2014 - 2018"
        ),
        "Certifications": (
            "- Google Cloud Professional Data Engineer (2023)"
        )
    }
    create_resume_pdf(
        "samples/resume_bob_data_scientist.pdf",
        "Bob Jones",
        "bob.jones@example.com",
        "+1-555-0248",
        "San Francisco, CA",
        bob_sections
    )
    
    # 3. Charlie Brown - Product Manager
    charlie_sections = {
        "Professional Summary": (
            "Results-driven Product Manager with 5+ years of experience leading cross-functional teams to launch B2B SaaS products. "
            "Expert in product roadmap formulation, backlog grooming, market analysis, and user experience design."
        ),
        "Core Competencies": (
            "- Product Management: Roadmap Planning, Agile/Scrum, User Stories, Product Lifecycle\n"
            "- Soft Skills: Stakeholder Management, Team Leadership, Communication, Problem Solving\n"
            "- Tools: Jira, Confluence, Figma, Mixpanel, Google Analytics"
        ),
        "Professional Experience": (
            "Product Manager | SaaSify Corp | March 2021 - Present\n"
            "- Led a cross-functional team of 10 engineers and designers to launch a new billing module, resulting in a 15% increase in MRR.\n"
            "- Defined product requirements and managed sprint cycles using Agile/Scrum methodologies in Jira.\n"
            "- Conducted 30+ user interviews to identify key customer pain points and outline the FY25 product roadmap.\n\n"
            "Associate Product Manager | BizGrowth | October 2018 - February 2021\n"
            "- Maintained product backlog, wrote detailed user stories, and collaborated with engineering to ensure on-time delivery.\n"
            "- Analyzed product usage metrics in Mixpanel to optimize user onboarding, reducing churn by 4%."
        ),
        "Education": (
            "Master of Business Administration (MBA)\n"
            "Global Business School | 2016 - 2018\n\n"
            "Bachelor of Business Administration (BBA)\n"
            "University of Commerce | 2012 - 2016"
        ),
        "Certifications": (
            "- Certified Scrum Product Owner (CSPO) (2019)"
        )
    }
    create_resume_pdf(
        "samples/resume_charlie_product_manager.pdf",
        "Charlie Brown",
        "charlie.brown@example.com",
        "+1-555-0377",
        "Austin, TX",
        charlie_sections
    )
    
    # 4. Write JD 1: Senior Python Developer
    jd_python = (
        "Role: Senior Python Developer\n"
        "Company: CloudSystems\n"
        "Location: New York, NY\n"
        "Employment Type: Full-time\n"
        "Industry: SaaS / Cloud Computing\n"
        "Domain: Backend Architecture\n\n"
        "Responsibilities:\n"
        "- Design, build, and maintain highly scalable backend services in Python.\n"
        "- Architect microservices using FastAPI or Django.\n"
        "- Configure cloud services on AWS, specifically AWS EC2 and AWS S3.\n"
        "- Build caching layers and queues using Redis.\n"
        "- Ensure robust version control and CI/CD pipelines.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- Django\n"
        "- FastAPI\n"
        "- AWS EC2\n"
        "- AWS S3\n"
        "- PostgreSQL\n"
        "- Docker\n"
        "- Git\n"
        "- Communication\n\n"
        "Preferred Skills:\n"
        "- Kubernetes\n"
        "- Redis\n"
        "- React\n"
        "- Node.js\n\n"
        "Experience & Education:\n"
        "- Minimum 5 years of professional software engineering experience.\n"
        "- Bachelor's Degree in Computer Science or equivalent STEM major.\n\n"
        "Mandatory Requirements:\n"
        "- Visa Status: Must be eligible to work in the US without sponsorship.\n"
        "- Location: Hybrid in New York, NY."
    )
    with open("samples/jd_senior_python_developer.txt", "w", encoding="utf-8") as f:
        f.write(jd_python)
        
    # 5. Write JD 2: Senior Data Scientist
    jd_ds = (
        "Role: Senior Data Scientist\n"
        "Company: DataLab Solutions\n"
        "Location: San Francisco, CA\n"
        "Employment Type: Full-time\n"
        "Industry: Artificial Intelligence\n"
        "Domain: Machine Learning & NLP\n\n"
        "Responsibilities:\n"
        "- Design and train machine learning and deep learning models to solve complex business problems.\n"
        "- Preprocess large structured and unstructured datasets.\n"
        "- Deploy production-grade ML pipelines on cloud infrastructure (GCP/AWS).\n"
        "- Perform advanced NLP tasks like sentiment classification and entity extraction.\n\n"
        "Required Skills:\n"
        "- Python\n"
        "- Scikit-Learn\n"
        "- PyTorch\n"
        "- Pandas\n"
        "- NumPy\n"
        "- SQL\n"
        "- Machine Learning\n\n"
        "Preferred Skills:\n"
        "- TensorFlow\n"
        "- SpaCy\n"
        "- Google Cloud Platform (GCP)\n"
        "- Tableau\n\n"
        "Experience & Education:\n"
        "- Minimum 4 years of data science experience.\n"
        "- Master's Degree in Data Science, Mathematics, Computer Science, or similar quantitative field.\n\n"
        "Mandatory Requirements:\n"
        "- Visa Status: Eligible to work in the US.\n"
        "- Location: San Francisco, CA."
    )
    with open("samples/jd_senior_data_scientist.txt", "w", encoding="utf-8") as f:
        f.write(jd_ds)
        
    print("Samples successfully generated in the 'samples/' directory.")

if __name__ == "__main__":
    main()
