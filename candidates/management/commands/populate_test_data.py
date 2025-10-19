"""
Test data creation command
Generates test data for candidates, jobs, skills, etc.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from candidates.models import (
    Candidate, CandidateProfile, CandidateSkill, Skill,
    Education, WorkExperience, Application
)
from jobs.models import Job, JobSkill, JobRequirement

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data (candidates, jobs, skills, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--candidates',
            type=int,
            default=15,
            help='Number of candidates to create (default: 15)'
        )
        parser.add_argument(
            '--jobs',
            type=int,
            default=12,
            help='Number of jobs to create (default: 12)'
        )

    def handle(self, *args, **options):
        num_candidates = options['candidates']
        num_jobs = options['jobs']

        self.stdout.write(self.style.SUCCESS('Starting test data creation...'))

        # Create skills
        self.create_skills()

        # Create candidates
        self.create_candidates(num_candidates)

        # Create jobs
        self.create_jobs(num_jobs)

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Test data creation completed!\n'
            f'   Candidates: {num_candidates}\n'
            f'   Jobs: {num_jobs}'
        ))

    def create_skills(self):
        """Create skill master data"""
        skills_data = [
            # Programming languages
            ('Python', 'programming'),
            ('JavaScript', 'programming'),
            ('TypeScript', 'programming'),
            ('Java', 'programming'),
            ('Go', 'programming'),
            ('Ruby', 'programming'),
            ('PHP', 'programming'),
            ('C++', 'programming'),
            ('C#', 'programming'),
            ('Swift', 'programming'),
            ('Kotlin', 'programming'),

            # Frameworks
            ('React', 'framework'),
            ('Vue.js', 'framework'),
            ('Angular', 'framework'),
            ('Next.js', 'framework'),
            ('Django', 'framework'),
            ('Flask', 'framework'),
            ('Spring Boot', 'framework'),
            ('Express.js', 'framework'),
            ('Rails', 'framework'),

            # Databases
            ('PostgreSQL', 'database'),
            ('MySQL', 'database'),
            ('MongoDB', 'database'),
            ('Redis', 'database'),
            ('Oracle', 'database'),

            # Cloud
            ('AWS', 'cloud'),
            ('Azure', 'cloud'),
            ('GCP', 'cloud'),
            ('Docker', 'cloud'),
            ('Kubernetes', 'cloud'),

            # Other
            ('Git', 'tool'),
            ('Linux', 'tool'),
            ('Machine Learning', 'other'),
            ('UI/UX Design', 'other'),
            ('Project Management', 'other'),
            ('Agile Development', 'other'),
        ]

        created_count = 0
        for name, category in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={'category': category}
            )
            if created:
                created_count += 1

        self.stdout.write(f'Skills: Created {created_count}')

    def create_candidates(self, count):
        """Create candidates and profiles"""

        first_names = ['John', 'Emily', 'Michael', 'Sarah', 'David', 'Jessica', 'Daniel', 'Lisa', 'James', 'Emma', 'Robert', 'Olivia', 'William', 'Sophia', 'Thomas']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson']

        positions = [
            'Frontend Engineer', 'Backend Engineer', 'Full Stack Engineer',
            'Data Scientist', 'DevOps Engineer', 'Product Manager',
            'UI Designer', 'QA Engineer', 'Security Engineer'
        ]

        skills = list(Skill.objects.all())

        for i in range(count):
            # Create user
            email = f'candidate{i+2}@example.com'

            # Skip existing users
            if User.objects.filter(email=email).exists():
                continue

            user = User.objects.create_user(
                email=email,
                password='password123',
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                phone=f'090-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
                role='candidate',
                is_verified=True
            )

            # Create candidate profile
            years_exp = random.randint(1, 15)
            candidate = Candidate.objects.create(
                user=user,
                date_of_birth=datetime(
                    random.randint(1985, 2000),
                    random.randint(1, 12),
                    random.randint(1, 28)
                ).date(),
                current_position=random.choice(positions),
                years_of_experience=years_exp,
                expected_salary=random.randint(400, 1200) * 10000,
                address='Shibuya, Tokyo',
                postal_code=f'{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                status='active'
            )

            # Profile details
            CandidateProfile.objects.create(
                candidate=candidate,
                summary=f'{years_exp} years of experience as a {candidate.current_position}. Worked on product development using modern technologies.',
                career_objective='Looking to leverage my technical skills in new challenges. Seeking an environment where I can contribute to the team while growing professionally.',
                preferred_location='Tokyo, Kanagawa',
                remote_work_preference=random.choice(['Fully Remote', 'Hybrid 2-3 days/week', 'Hybrid', 'Office-based']),
                willing_to_relocate=random.choice([True, False]),
                japanese_level='Native',
                english_level=random.choice(['Beginner', 'Intermediate', 'Advanced', 'Business Level'])
            )

            # Add skills (3-8)
            num_skills = random.randint(3, 8)
            candidate_skills = random.sample(skills, min(num_skills, len(skills)))
            proficiency_levels = ['beginner', 'intermediate', 'advanced', 'expert']

            for skill in candidate_skills:
                CandidateSkill.objects.create(
                    candidate=candidate,
                    skill=skill,
                    proficiency_level=random.choice(proficiency_levels),
                    years_of_experience=random.randint(1, min(years_exp, 10))
                )

            # Add education
            Education.objects.create(
                candidate=candidate,
                institution_name='State University',
                degree='bachelor',
                field_of_study='Computer Science' if random.random() > 0.5 else 'Economics',
                start_date=datetime(random.randint(2005, 2015), 4, 1).date(),
                end_date=datetime(random.randint(2009, 2019), 3, 31).date(),
                is_current=False
            )

            # Add work experience (1-3 entries)
            start_year = 2024 - years_exp
            for j in range(random.randint(1, min(3, years_exp))):
                years_at_company = random.randint(2, 5)
                WorkExperience.objects.create(
                    candidate=candidate,
                    company_name=f'{random.choice(["Tech", "Software", "Digital", "Innovation"])} Corp',
                    position=random.choice(positions),
                    start_date=datetime(start_year + j * 2, random.randint(1, 12), 1).date(),
                    end_date=datetime(start_year + j * 2 + years_at_company, random.randint(1, 12), 28).date() if j < 2 else None,
                    is_current=(j == 0),
                    description='Responsible for project design, development, and operation. Worked with team members on agile development.',
                    location='Tokyo'
                )

        self.stdout.write(f'Candidates: Created {count}')

    def create_jobs(self, count):
        """Create jobs"""

        # Get recruiter user
        recruiter = User.objects.filter(role='recruiter').first()
        if not recruiter:
            self.stdout.write(self.style.WARNING('Recruiter user not found'))
            return

        job_titles = [
            'Senior Frontend Engineer', 'Backend Engineer', 'Full Stack Engineer',
            'Data Scientist', 'DevOps Engineer', 'Product Manager',
            'Mobile App Engineer (iOS)', 'Mobile App Engineer (Android)',
            'SRE Engineer', 'Security Engineer', 'QA Engineer', 'Tech Lead'
        ]

        departments = ['Engineering', 'Development', 'Product Development', 'Technology', 'R&D']
        locations = ['Shibuya, Tokyo', 'Minato, Tokyo', 'Chiyoda, Tokyo', 'Yokohama, Kanagawa', 'Osaka']

        employment_types = ['full_time', 'contract', 'part_time']
        experience_levels = ['junior', 'mid', 'senior', 'lead']

        skills = list(Skill.objects.all())

        for i in range(count):
            title = random.choice(job_titles)
            exp_level = random.choice(experience_levels)

            # Set salary range based on experience level
            if exp_level == 'junior':
                salary_min = random.randint(400, 500) * 10000
                salary_max = random.randint(600, 700) * 10000
            elif exp_level == 'mid':
                salary_min = random.randint(500, 700) * 10000
                salary_max = random.randint(800, 1000) * 10000
            elif exp_level == 'senior':
                salary_min = random.randint(700, 900) * 10000
                salary_max = random.randint(1100, 1400) * 10000
            else:  # lead
                salary_min = random.randint(900, 1200) * 10000
                salary_max = random.randint(1400, 2000) * 10000

            job = Job.objects.create(
                title=title,
                job_code=f'JOB-{random.randint(10000, 99999)}',
                department=random.choice(departments),
                location=random.choice(locations),
                remote_work_option=random.choice(['Fully Remote', 'Hybrid 2-3 days/week', 'Hybrid', '']),
                employment_type=random.choice(employment_types),
                experience_level=exp_level,
                description=f'Work on product development as a {title} using modern technologies.',
                responsibilities='- Product design and development\n- Code review\n- Collaboration with team members',
                qualifications='- 3+ years of experience in related technologies\n- Team development experience\n- Experience using Git/GitHub',
                preferred_qualifications='- OSS contribution experience\n- Technical blog writing experience\n- English communication skills',
                salary_min=salary_min,
                salary_max=salary_max,
                benefits='- Full social insurance coverage\n- Remote work available\n- Book purchase assistance\n- Certification support',
                number_of_positions=random.randint(1, 3),
                deadline=(timezone.now() + timedelta(days=random.randint(30, 90))).date(),
                status=random.choice(['draft', 'active', 'active', 'active']),  # More active ones
                is_featured=random.random() > 0.7,
                hiring_manager=recruiter
            )

            # Add job skills (3-6)
            num_skills = random.randint(3, 6)
            job_skills = random.sample(skills, min(num_skills, len(skills)))

            for skill in job_skills:
                JobSkill.objects.create(
                    job=job,
                    skill=skill,
                    requirement_level=random.choice(['required', 'preferred', 'optional']),
                    minimum_proficiency=random.choice(['intermediate', 'advanced', 'expert']),
                    minimum_years=random.randint(1, 5),
                    weight=random.randint(5, 10)
                )

            # Add job requirements
            JobRequirement.objects.create(
                job=job,
                requirement_type='must_have',
                category='skill',
                description='Practical experience with specified technologies',
                priority=1
            )
            JobRequirement.objects.create(
                job=job,
                requirement_type='nice_to_have',
                category='skill',
                description='Interest and willingness to learn related technologies',
                priority=2
            )

        self.stdout.write(f'Jobs: Created {count}')
