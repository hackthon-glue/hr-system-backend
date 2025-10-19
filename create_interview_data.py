#!/usr/bin/env python
"""
Interview test data creation script
Creates interview data for candidate@example.com user
"""
import os
import sys
import django
from datetime import timedelta

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_agent_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from candidates.models import Candidate, Application, Interview
from jobs.models import Job

User = get_user_model()

def create_interview_data():
    """Create interview data"""

    print("=" * 60)
    print("Interview Test Data Creation")
    print("=" * 60)

    # Get candidate@example.com user
    try:
        user = User.objects.get(email='candidate@example.com')
        candidate = user.candidate
        print(f"✓ Retrieved candidate: {user.get_full_name()} ({user.email})")
    except User.DoesNotExist:
        print("✗ Error: candidate@example.com user not found")
        return
    except Candidate.DoesNotExist:
        print("✗ Error: Candidate profile not found")
        return

    # Get open jobs
    jobs = Job.objects.filter(status='open')[:3]
    if not jobs:
        print("✗ Error: No open jobs found")
        return

    print(f"\n✓ Found {len(jobs)} jobs")

    # Get or create interviewer user
    interviewer_user, created = User.objects.get_or_create(
        email='interviewer@example.com',
        defaults={
            'first_name': 'Alex',
            'last_name': 'Johnson',
            'role': 'interviewer'
        }
    )
    if created:
        interviewer_user.set_password('interviewer123')
        interviewer_user.save()
        print(f"✓ Created interviewer user: {interviewer_user.get_full_name()}")
    else:
        print(f"✓ Retrieved interviewer user: {interviewer_user.get_full_name()}")

    # Get or create recruiter user
    recruiter_user, created = User.objects.get_or_create(
        email='recruiter@example.com',
        defaults={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'recruiter'
        }
    )
    if created:
        recruiter_user.set_password('recruiter123')
        recruiter_user.save()
        print(f"✓ Created recruiter user: {recruiter_user.get_full_name()}")
    else:
        print(f"✓ Retrieved recruiter user: {recruiter_user.get_full_name()}")

    print("\n" + "=" * 60)
    print("Creating applications and interviews...")
    print("=" * 60)

    # Create applications and interviews for each job
    interview_count = 0

    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}/{len(jobs)}] {job.title}")

        # Create or get application
        application, app_created = Application.objects.get_or_create(
            candidate=candidate,
            job=job,
            defaults={
                'status': 'interview_scheduled',
                'cover_letter': f'I am applying for the {job.title} position. I believe my experience and skills match your requirements.',
                'matching_score': 85 + i * 2,
                'assigned_recruiter': recruiter_user,
                'screening_notes': 'Skill set matches requirements. Proceed to interview.',
            }
        )

        if app_created:
            print(f"  ✓ Created application (ID: {application.id}, Status: {application.get_status_display()})")
        else:
            # Update existing application status
            if application.status not in ['interview_scheduled', 'offer_extended', 'offer_accepted']:
                application.status = 'interview_scheduled'
                application.assigned_recruiter = recruiter_user
                application.save()
                print(f"  ✓ Updated existing application (ID: {application.id}, Status: {application.get_status_display()})")
            else:
                print(f"  - Application already exists (ID: {application.id}, Status: {application.get_status_display()})")

        # Set interview types and schedules
        interview_types = [
            {
                'type': 'phone_screen',
                'round': 1,
                'days_from_now': 2,
                'duration': 30,
                'result': 'pending',
                'notes': 'First phone screening'
            },
            {
                'type': 'technical',
                'round': 2,
                'days_from_now': 7,
                'duration': 90,
                'result': 'pending',
                'notes': 'Technical interview'
            },
            {
                'type': 'behavioral',
                'round': 3,
                'days_from_now': 14,
                'duration': 60,
                'result': 'pending',
                'notes': 'Final interview'
            }
        ]

        # Set different interview patterns for each job
        if i == 1:
            # First job: All interviews setup (first completed, second scheduled, final TBD)
            interviews_to_create = interview_types
            interviews_to_create[0]['result'] = 'passed'
            interviews_to_create[0]['technical_score'] = 8
            interviews_to_create[0]['communication_score'] = 9
            interviews_to_create[0]['cultural_fit_score'] = 8
            interviews_to_create[0]['overall_score'] = 8
            interviews_to_create[0]['feedback'] = 'Strong technical knowledge and excellent communication skills.'
            interviews_to_create[0]['strengths'] = 'Proficient in Python, React, and Django'
            interviews_to_create[0]['days_from_now'] = -3  # Completed 3 days ago
        elif i == 2:
            # Second job: Only first interview scheduled
            interviews_to_create = [interview_types[0]]
        else:
            # Third job: First and second interviews setup
            interviews_to_create = interview_types[:2]

        # Create interviews
        for interview_data in interviews_to_create:
            scheduled_date = timezone.now() + timedelta(days=interview_data['days_from_now'])

            interview, interview_created = Interview.objects.get_or_create(
                application=application,
                interview_type=interview_data['type'],
                round_number=interview_data['round'],
                defaults={
                    'scheduled_date': scheduled_date,
                    'duration_minutes': interview_data['duration'],
                    'result': interview_data.get('result'),
                    'technical_score': interview_data.get('technical_score'),
                    'communication_score': interview_data.get('communication_score'),
                    'cultural_fit_score': interview_data.get('cultural_fit_score'),
                    'overall_score': interview_data.get('overall_score'),
                    'feedback': interview_data.get('feedback', ''),
                    'strengths': interview_data.get('strengths', ''),
                    'notes': interview_data['notes']
                }
            )

            if interview_created:
                # Add interviewer
                interview.interviewers.add(interviewer_user)
                interview_count += 1

                status_text = f"Completed ({interview.get_result_display()})" if interview.result else "Scheduled"
                print(f"  ✓ Created interview: {interview.get_interview_type_display()} (Round {interview.round_number}) - {status_text}")
                print(f"    - Date/Time: {scheduled_date.strftime('%Y/%m/%d %H:%M')}")
                print(f"    - Duration: {interview.duration_minutes} minutes")
                if interview.result:
                    print(f"    - Overall Score: {interview.overall_score}/10")
            else:
                print(f"  - Interview already exists: {interview.get_interview_type_display()} (Round {interview.round_number})")

    print("\n" + "=" * 60)
    print(f"✓ Completed: Created {interview_count} interviews")
    print("=" * 60)

    print("\n【Login Credentials】")
    print(f"Candidate: candidate@example.com / candidate123")
    print(f"Interviewer: interviewer@example.com / interviewer123")
    print(f"Recruiter: recruiter@example.com / recruiter123")

    print("\n【Next Steps】")
    print("1. Login with candidate@example.com")
    print("2. Check applications on 'Applications' page")
    print("3. View interview schedule on application detail page")
    print("4. (Future) Take interview on interview page")

if __name__ == '__main__':
    create_interview_data()
