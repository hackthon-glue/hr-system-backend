#!/usr/bin/env python
"""
Job data creation script
Creates jobs that match candidate@example.com (John Doe)
"""
import os
import sys
import django

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_agent_system.settings')
django.setup()

from jobs.models import Job, JobSkill
from candidates.models import Skill
from authz.models import User

def create_jobs():
    """Create job data"""

    # Get recruiter user
    try:
        recruiter = User.objects.get(email='recruiter@example.com')
    except User.DoesNotExist:
        print("Recruiter user not found. Creating...")
        recruiter = User.objects.create_user(
            email='recruiter@example.com',
            password='password123',
            first_name='Jane',
            last_name='Smith',
            role='recruiter'
        )

    # Get skills
    python_skill = Skill.objects.get(name='Python')
    javascript_skill = Skill.objects.get(name='JavaScript')
    typescript_skill = Skill.objects.get(name='TypeScript')
    react_skill = Skill.objects.get(name='React')
    django_skill = Skill.objects.get(name='Django')
    fastapi_skill = Skill.objects.get(name='FastAPI')

    jobs_data = [
        {
            'job_code': 'JOB-2025-001',
            'title': 'Senior Backend Engineer (Python/Django)',
            'department': 'Technology',
            'description': '''We are seeking a Senior Backend Engineer to lead the development of our next-generation HR system at a major IT company.

【Development Environment】
- Language: Python 3.11+
- Framework: Django, FastAPI
- Database: PostgreSQL, Redis
- Infrastructure: AWS (ECS, RDS, ElastiCache)
- Others: Docker, Kubernetes, CI/CD (GitHub Actions)''',
            'responsibilities': '''- Design and develop RESTful APIs using Django/FastAPI
- Design and implement microservices architecture
- Database design and optimization
- Code review and technical leadership''',
            'qualifications': '''・5+ years of Python development experience
・API development experience with Django/FastAPI
・Database design experience
・Team development experience
・Bachelor's degree or higher
・Computer Science or related field degree''',
            'preferred_qualifications': '''・Microservices development experience
・AWS experience
・Agile development experience
・Technical documentation writing skills in English''',
            'salary_min': 9000000,
            'salary_max': 14000000,
            'location': 'Shibuya, Tokyo (Remote available)',
            'employment_type': 'full_time',
            'experience_level': 'senior',
            'status': 'active',
            'hiring_manager': recruiter,
            'skills': [
                (python_skill, 'required', 'advanced', 5),
                (django_skill, 'required', 'intermediate', 3),
                (fastapi_skill, 'preferred', 'intermediate', 2),
            ]
        },
        {
            'job_code': 'JOB-2025-002',
            'title': 'Full Stack Engineer (React/TypeScript/Python)',
            'department': 'Engineering',
            'description': '''We are seeking a Full Stack Engineer who can work on both frontend and backend at a rapidly growing startup.

【Development Environment】
- Frontend: React, Next.js, TypeScript
- Backend: Python, FastAPI
- Database: PostgreSQL
- Infrastructure: AWS (Lambda, API Gateway, RDS)''',
            'responsibilities': '''- Frontend development using React/Next.js
- Backend API development using Python/FastAPI
- Building and improving CI/CD pipelines
- Technology selection and architecture design''',
            'qualifications': '''・3+ years of React development experience
・2+ years of TypeScript experience
・Python/FastAPI experience
・REST API design experience
・Bachelor's degree or higher''',
            'preferred_qualifications': '''・Next.js experience
・Serverless architecture experience
・Startup experience''',
            'salary_min': 8000000,
            'salary_max': 13000000,
            'location': 'Minato, Tokyo (Fully remote available)',
            'employment_type': 'full_time',
            'experience_level': 'senior',
            'status': 'active',
            'hiring_manager': recruiter,
            'skills': [
                (react_skill, 'required', 'advanced', 3),
                (typescript_skill, 'required', 'intermediate', 2),
                (python_skill, 'required', 'intermediate', 3),
                (fastapi_skill, 'preferred', 'intermediate', 2),
            ]
        },
        {
            'job_code': 'JOB-2025-003',
            'title': 'Tech Lead (Python/JavaScript)',
            'department': 'Engineering',
            'description': '''We are seeking a Tech Lead to lead the development of our enterprise SaaS product.

【Development Environment】
- Backend: Python, Django, FastAPI
- Frontend: React, TypeScript
- Database: PostgreSQL, MongoDB
- Infrastructure: AWS, Docker, Kubernetes''',
            'responsibilities': '''- Technical leadership for development team (5-8 members)
- Full-stack development using Python/JavaScript
- Architecture design and technology selection
- Code review and mentoring''',
            'qualifications': '''・5+ years of development experience with both Python and JavaScript
・Team lead experience
・Architecture design experience
・Mentoring experience
・Bachelor's degree or higher
・Computer Science related degree''',
            'preferred_qualifications': '''・Management experience with teams of 10+ members
・Technical blog writing or speaking experience
・OSS contribution experience''',
            'salary_min': 11000000,
            'salary_max': 16000000,
            'location': 'Chiyoda, Tokyo',
            'employment_type': 'full_time',
            'experience_level': 'lead',
            'status': 'active',
            'hiring_manager': recruiter,
            'skills': [
                (python_skill, 'required', 'expert', 5),
                (javascript_skill, 'required', 'advanced', 5),
                (react_skill, 'preferred', 'advanced', 3),
                (django_skill, 'preferred', 'intermediate', 3),
            ]
        },
        {
            'job_code': 'JOB-2025-004',
            'title': 'Backend Engineer (Python/Django)',
            'department': 'Product Development',
            'description': '''We are seeking an Engineer to work on backend development for a large-scale e-commerce site.

【Development Environment】
- Language: Python 3.10+
- Framework: Django, DRF
- Database: PostgreSQL, Redis
- Infrastructure: AWS (EC2, RDS, ElastiCache)''',
            'responsibilities': '''- Backend API development using Django
- Database design and optimization
- Performance tuning
- Design and implementation of new features''',
            'qualifications': '''・4+ years of Python development experience
・2+ years of Django experience
・SQL database experience
・Git usage experience
・Bachelor's degree or higher''',
            'preferred_qualifications': '''・E-commerce development experience
・Large-scale traffic handling experience
・Performance tuning experience''',
            'salary_min': 8500000,
            'salary_max': 12000000,
            'location': 'Shinjuku, Tokyo (Hybrid 2 days/week remote)',
            'employment_type': 'full_time',
            'experience_level': 'mid',
            'status': 'active',
            'hiring_manager': recruiter,
            'skills': [
                (python_skill, 'required', 'advanced', 4),
                (django_skill, 'required', 'intermediate', 2),
            ]
        },
        {
            'job_code': 'JOB-2025-005',
            'title': 'Frontend Engineer (React/TypeScript)',
            'department': 'UI/UX Development',
            'description': '''We are seeking an Engineer to lead web application development using modern frontend technologies.

【Development Environment】
- Language: TypeScript
- Framework: React, Next.js
- State Management: Redux, Zustand
- Styling: Tailwind CSS
- Testing: Jest, React Testing Library''',
            'responsibilities': '''- SPA development using React/Next.js
- Component design and state management
- Performance optimization
- Collaboration with designers''',
            'qualifications': '''・3+ years of React development experience
・2+ years of TypeScript experience
・Component design experience
・Responsive design implementation experience
・Bachelor's degree or higher''',
            'preferred_qualifications': '''・Next.js experience
・Performance optimization experience
・Accessibility implementation experience''',
            'salary_min': 7500000,
            'salary_max': 11000000,
            'location': 'Minato, Tokyo (Remote available)',
            'employment_type': 'full_time',
            'experience_level': 'senior',
            'status': 'active',
            'hiring_manager': recruiter,
            'skills': [
                (react_skill, 'required', 'advanced', 3),
                (typescript_skill, 'required', 'intermediate', 2),
                (javascript_skill, 'required', 'advanced', 4),
            ]
        },
    ]

    print("Creating jobs...")
    created_jobs = []

    for job_data in jobs_data:
        # Separate skill information
        skills_info = job_data.pop('skills', [])

        # Create job (skip if already exists)
        job, created = Job.objects.get_or_create(
            job_code=job_data['job_code'],
            defaults=job_data
        )

        if created:
            print(f"✓ Created: {job.title} ({job.job_code})")

            # Add skill requirements
            for skill, requirement_level, minimum_proficiency, minimum_years in skills_info:
                JobSkill.objects.create(
                    job=job,
                    skill=skill,
                    requirement_level=requirement_level,
                    minimum_proficiency=minimum_proficiency,
                    minimum_years=minimum_years
                )

            created_jobs.append(job)
        else:
            print(f"- Already exists: {job.title} ({job.job_code})")

    print(f"\n{len(created_jobs)} new jobs created successfully!")
    print(f"Total open jobs: {Job.objects.filter(status='open').count()}")

    return created_jobs

if __name__ == '__main__':
    create_jobs()
