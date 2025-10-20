# HR AI Agent System - Simple Testing Guide (GUI-Based)

## Prerequisites

```bash
# Start the backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python create_superuser.py  # admin@example.com / admin123456
python manage.py runserver
```

## 1. Django Admin UI Testing

### Access
- URL: http://localhost:8000/admin/
- Credentials: `admin@example.com` / `admin123456`

### Test Items

#### 1.1 User Management
- [ ] Create new user from **Users**
  - Set Email, password, and role (candidate/recruiter/interviewer/admin)
  - **Note**: Username field is NOT used (email is the primary key)

#### 1.2 Candidate Management
- [ ] Create candidate profile from **Candidates**
  - Link to a user
  - Enter basic info (name, phone, address, etc.)
- [ ] Add skills from **Candidate skills**
- [ ] Add education from **Educations**
- [ ] Add work experience from **Work experiences**

#### 1.3 Job Management
- [ ] Create job from **Jobs**
  - Enter title, description, salary range, location, etc.
  - Set status (draft/open/closed)
- [ ] Add requirements from **Job requirements**
- [ ] Add required skills from **Job skills**

#### 1.4 Application Management
- [ ] Create application from **Applications**
  - Select candidate and job
  - Check status (applied/screening/interview/offered/rejected)

#### 1.5 Interview Management
- [ ] Create interview from **Interviews**
  - Link to an application
  - Set interview date/time, interviewer, and status

#### 1.6 Audit Logs
- [ ] Check operation history in **Audit logs**
  - Verify user, HTTP method, path, and status code

---

## 2. Swagger UI API Testing

### Access
- URL: http://localhost:8000/swagger/

### Test Items

#### 2.1 Candidates API
- [ ] **GET /api/candidates/candidates/** - List candidates
- [ ] **POST /api/candidates/candidates/** - Create new candidate
  ```json
  {
    "user": 1,
    "full_name": "John Doe",
    "phone_number": "090-1234-5678",
    "address": "Tokyo, Shibuya"
  }
  ```
- [ ] **GET /api/candidates/candidates/{id}/** - Get candidate details
- [ ] **PUT/PATCH /api/candidates/candidates/{id}/** - Update candidate
- [ ] **DELETE /api/candidates/candidates/{id}/** - Delete candidate

#### 2.2 Candidate Skills API
- [ ] **GET /api/candidates/candidates/{id}/skills/** - List candidate skills
- [ ] **POST /api/candidates/skills/** - Add skill
  ```json
  {
    "candidate": 1,
    "skill_name": "Python",
    "proficiency_level": "expert",
    "years_of_experience": 5
  }
  ```

#### 2.3 Jobs API
- [ ] **GET /api/jobs/jobs/** - List jobs (test filtering)
  - Query params: `?status=open&location=Tokyo`
- [ ] **POST /api/jobs/jobs/** - Create new job
  ```json
  {
    "title": "Backend Engineer",
    "description": "Django development",
    "requirements": "3+ years Python experience",
    "location": "Tokyo",
    "employment_type": "full_time",
    "salary_min": 6000000,
    "salary_max": 10000000,
    "status": "open"
  }
  ```
- [ ] **GET /api/jobs/jobs/{id}/** - Get job details

#### 2.4 Applications API
- [ ] **GET /api/jobs/applications/** - List applications
- [ ] **POST /api/jobs/applications/** - Create new application
  ```json
  {
    "candidate": 1,
    "job": 1,
    "cover_letter": "I am interested in this position",
    "status": "applied"
  }
  ```
- [ ] **PATCH /api/jobs/applications/{id}/** - Update application status
  ```json
  {
    "status": "interview"
  }
  ```

#### 2.5 Interviews API
- [ ] **GET /api/jobs/interviews/** - List interviews
- [ ] **POST /api/jobs/interviews/** - Schedule interview
  ```json
  {
    "application": 1,
    "scheduled_at": "2025-10-25T10:00:00Z",
    "interviewer": 2,
    "interview_type": "technical",
    "status": "scheduled"
  }
  ```

---

## 3. Testing with Sample Data

### Create Sample Data

```bash
cd backend
python create_sample_data.py    # Candidate data
python create_job_data.py        # Job data
python create_interview_data.py  # Interview data
```

### Verification
- [ ] Data appears in Admin UI
- [ ] GET APIs return data in Swagger UI
- [ ] Relationships (candidate→application→interview) are correct

---

## 4. End-to-End Scenario Testing

### Scenario: From Application to Interview

1. [ ] **Create User** (Admin UI)
   - Create user with candidate role

2. [ ] **Create Candidate Profile** (Admin UI or Swagger)
   - Register basic info, skills, education, work experience

3. [ ] **Create Job** (Admin UI)
   - Create job with open status
   - Set required skills

4. [ ] **Create Application** (Swagger)
   - POST /api/jobs/applications/ - Candidate applies to job
   - status: applied

5. [ ] **Update Application Status** (Swagger)
   - PATCH /api/jobs/applications/{id}/ - screening → interview

6. [ ] **Create Interview** (Admin UI or Swagger)
   - Schedule interview linked to application
   - Assign interviewer

7. [ ] **Update Interview After Completion** (Swagger)
   - PATCH /api/jobs/interviews/{id}/ - Set to completed
   - Add feedback

8. [ ] **Check Audit Logs** (Admin UI)
   - Verify all operations are logged

---

## 5. Error Case Testing

### Validation Errors
- [ ] POST without required fields → 400 Bad Request
- [ ] GET with non-existent ID → 404 Not Found
- [ ] Invalid email format → Validation error
- [ ] Duplicate email for user creation → Error

### Permission Errors (after implementation)
- [ ] Unauthenticated access → 401 Unauthorized
- [ ] Unauthorized operation → 403 Forbidden

---

## 6. Other Checks

### Performance
- [ ] Pagination with large datasets
- [ ] Filtering and search functionality

### Data Integrity
- [ ] Foreign key constraints (linking with non-existent ID)
- [ ] CASCADE delete behavior

### Logging
- [ ] Log files generated in `backend/logs/`
- [ ] HTTP requests recorded in Audit logs

---

## Important Notes

- **Authentication not implemented**: JWT settings exist but endpoints are not implemented
- **Frontend not implemented**: Next.js directory is empty
- **AWS Bedrock not integrated**: Agent features planned for future
- **Development environment**: Uses SQLite (PostgreSQL recommended for production)

---

## Troubleshooting

### Error: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Error: logs directory not found
```bash
mkdir -p logs static media
```

### Reset Database
```bash
rm db.sqlite3
python manage.py migrate
python create_superuser.py
```

---

By following these test items in order, you can verify the basic functionality of the system.
