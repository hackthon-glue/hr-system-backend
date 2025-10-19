#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_agent_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

from django.utils import timezone
from authz.models import User
from candidates.models import Candidate, Skill, CandidateSkill, Education, WorkExperience
from jobs.models import Job, JobSkill, JobRequirement

def create_users():
    """Create test users"""
    users = []

    # Candidate user
    candidate_user, created = User.objects.get_or_create(
        email='candidate@example.com',
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'candidate'
        }
    )
    if created:
        candidate_user.set_password('password123')
        candidate_user.save()
        print("Created candidate user")
    else:
        print("Candidate user already exists")
    users.append(candidate_user)

    # Recruiter user
    recruiter_user, created = User.objects.get_or_create(
        email='recruiter@example.com',
        defaults={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'recruiter'
        }
    )
    if created:
        recruiter_user.set_password('password123')
        recruiter_user.save()
        print("Created recruiter user")
    else:
        print("Recruiter user already exists")
    users.append(recruiter_user)

    return users

def create_skills():
    """Create skill master data"""
    skills_data = [
        # Programming languages
        ('Python', 'programming', 'Programming language'),
        ('JavaScript', 'programming', 'Programming language'),
        ('TypeScript', 'programming', 'Programming language'),
        ('Java', 'programming', 'Programming language'),
        ('Go', 'programming', 'Programming language'),

        # Frameworks
        ('Django', 'framework', 'Python web framework'),
        ('React', 'framework', 'JavaScript UI library'),
        ('Next.js', 'framework', 'React framework'),
        ('Spring Boot', 'framework', 'Java framework'),
        ('FastAPI', 'framework', 'Python API framework'),

        # Databases
        ('PostgreSQL', 'database', 'Relational database'),
        ('MySQL', 'database', 'Relational database'),
        ('MongoDB', 'database', 'NoSQL database'),
        ('Redis', 'database', 'In-memory database'),

        # Cloud
        ('AWS', 'cloud', 'Amazon Web Services'),
        ('GCP', 'cloud', 'Google Cloud Platform'),
        ('Azure', 'cloud', 'Microsoft Azure'),
        ('Docker', 'tools', 'Container technology'),
        ('Kubernetes', 'tools', 'Container orchestration'),

        # Soft skills
        ('Leadership', 'soft_skill', 'Ability to lead teams'),
        ('Communication', 'soft_skill', 'Effective communication skills'),
        ('Problem Solving', 'soft_skill', 'Problem-solving abilities'),
        ('Project Management', 'soft_skill', 'Project management abilities'),
    ]

    skills = []
    for name, category, description in skills_data:
        skill, created = Skill.objects.get_or_create(
            name=name,
            defaults={
                'category': category,
                'description': description
            }
        )
        skills.append(skill)

    print(f"Created {len(skills)} skills")
    return skills

def create_candidates(users, skills):
    """Create candidate data"""
    candidate_user = users[0]  # Use first user as candidate

    # Check if candidate already exists
    try:
        candidate = Candidate.objects.get(user=candidate_user)
        print(f"Candidate profile already exists for {candidate_user.email}")
    except Candidate.DoesNotExist:
        candidate = Candidate.objects.create(
            user=candidate_user,
            date_of_birth=date(1990, 5, 15),
            gender='male',
            nationality='USA',
            address='Shibuya, Tokyo',
            postal_code='150-0001',
            current_position='Senior Engineer @ Tech Corp',
            years_of_experience=8,
            status='active',
            expected_salary=10000000,
            portfolio_url='https://portfolio.example.com',
            github_url='https://github.com/example',
            linkedin_url='https://linkedin.com/in/example'
        )
        print(f"Created candidate profile for {candidate_user.email}")

    # Add skills (avoid duplicates)
    skill_levels = ['expert', 'advanced', 'intermediate']
    for i, skill in enumerate(skills[:10]):  # Add first 10 skills
        CandidateSkill.objects.get_or_create(
            candidate=candidate,
            skill=skill,
            defaults={
                'proficiency_level': skill_levels[i % 3],
                'years_of_experience': max(1, 8 - i)
            }
        )

    # Add education (avoid duplicates)
    Education.objects.get_or_create(
        candidate=candidate,
        institution_name='State University',
        defaults={
            'degree': 'bachelor',
            'field_of_study': 'Computer Science',
            'start_date': date(2008, 4, 1),
            'end_date': date(2012, 3, 31),
            'gpa': Decimal('3.5'),
            'description': 'Majored in Computer Science'
        }
    )

    # Add work experience (avoid duplicates)
    WorkExperience.objects.get_or_create(
        candidate=candidate,
        company_name='Tech Corp',
        defaults={
            'position': 'Senior Engineer',
            'employment_type': 'Full-time',
            'start_date': date(2018, 4, 1),
            'is_current': True,
            'description': 'Lead engineer for web application development',
            'achievements': 'Introduced microservices architecture',
            'technologies_used': 'Python, Django, React, AWS',
            'team_size': 10
        }
    )

    WorkExperience.objects.get_or_create(
        candidate=candidate,
        company_name='Startup Inc',
        defaults={
            'position': 'Software Engineer',
            'employment_type': 'Full-time',
            'start_date': date(2012, 4, 1),
            'end_date': date(2018, 3, 31),
            'is_current': False,
            'description': 'Web application development',
            'achievements': 'Improved quality through automated testing',
            'technologies_used': 'Ruby on Rails, JavaScript, PostgreSQL',
            'team_size': 5
        }
    )

    print(f"Created candidate with profile, skills, education, and work experience")
    return candidate

def create_jobs(users, skills):
    """Create job data"""
    recruiter_user = users[1]  # Use second user as recruiter

    jobs = []

    # Senior engineer position
    job1, created = Job.objects.get_or_create(
        title='Senior Backend Engineer',
        job_code='BE-2025-001',
        defaults={
            'department': 'Engineering',
            'location': 'Tokyo',
            'employment_type': 'full_time',
            'experience_level': 'senior',
            'description': 'Lead backend system design and development',
            'responsibilities': '・System architecture design\n・Code review\n・Mentoring junior members',
            'qualifications': '・Computer Science degree or related field\n・Experience developing large-scale systems',
            'salary_min': 8000000,
            'salary_max': 12000000,
            'benefits': '・Remote work available\n・Flexible hours\n・Training programs available',
            'status': 'published',
            'hiring_manager': recruiter_user,
            'published_date': timezone.now(),
            'deadline': (timezone.now() + timedelta(days=60)).date()
        }
    )
    jobs.append(job1)

    # Frontend engineer position
    job2, created = Job.objects.get_or_create(
        title='Frontend Engineer',
        job_code='FE-2025-001',
        defaults={
            'department': 'Engineering',
            'location': 'Tokyo',
            'employment_type': 'full_time',
            'experience_level': 'mid',
            'description': 'Modern web application frontend development',
            'responsibilities': '・Development using React/Next.js\n・UI/UX improvement proposals\n・Performance optimization',
            'qualifications': '・Practical experience with React, TypeScript\n・Experience implementing responsive design',
            'salary_min': 6000000,
            'salary_max': 9000000,
            'benefits': '・Remote work available\n・Book purchase assistance\n・Conference participation support',
            'status': 'published',
            'hiring_manager': recruiter_user,
            'published_date': timezone.now(),
            'deadline': (timezone.now() + timedelta(days=45)).date()
        }
    )
    jobs.append(job2)

    # Add skill requirements to jobs
    for job in jobs:
        # Required skills
        for skill in skills[:5]:
            JobSkill.objects.get_or_create(
                job=job,
                skill=skill,
                defaults={
                    'requirement_level': 'required',
                    'minimum_proficiency': 'intermediate',
                    'minimum_years': 2,
                    'weight': Decimal('1.0')
                }
            )

        # Preferred skills
        for skill in skills[5:8]:
            JobSkill.objects.get_or_create(
                job=job,
                skill=skill,
                defaults={
                    'requirement_level': 'preferred',
                    'minimum_proficiency': 'beginner',
                    'minimum_years': 1,
                    'weight': Decimal('0.5')
                }
            )

        # Add job requirements
        JobRequirement.objects.get_or_create(
            job=job,
            requirement_type='must_have',
            category='experience',
            defaults={
                'description': '5+ years of backend development experience',
                'priority': 1
            }
        )

        JobRequirement.objects.get_or_create(
            job=job,
            requirement_type='nice_to_have',
            category='certification',
            defaults={
                'description': 'AWS certification',
                'priority': 2
            }
        )

    print(f"Created {len(jobs)} jobs with requirements and skills")
    return jobs

def main():
    """Main process"""
    print("Starting sample data creation...")

    try:
        # Create users
        users = create_users()

        # Create skill master
        skills = create_skills()

        # Create candidates
        candidate = create_candidates(users, skills)

        # Create jobs
        jobs = create_jobs(users, skills)

        print("\n✅ Sample data created successfully!")
        print("\nYou can now login with:")
        print("  Candidate: candidate@example.com / password123")
        print("  Recruiter: recruiter@example.com / password123")
        print("  Admin: admin@example.com / admin123456")

    except Exception as e:
        print(f"\n❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
