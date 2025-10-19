"""
応募と面接のテストデータ作成コマンド
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from candidates.models import Candidate, Application, Interview
from jobs.models import Job


class Command(BaseCommand):
    help = '応募と面接のテストデータを作成します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--applications',
            type=int,
            default=30,
            help='作成する応募の数（デフォルト: 30）'
        )

    def handle(self, *args, **options):
        num_applications = options['applications']

        self.stdout.write(self.style.SUCCESS('応募・面接データ作成を開始します...'))

        # 既存データ確認
        candidates = list(Candidate.objects.filter(status='active'))
        jobs = list(Job.objects.filter(status='active'))

        if not candidates:
            self.stdout.write(self.style.ERROR('アクティブな候補者が見つかりません'))
            return

        if not jobs:
            self.stdout.write(self.style.ERROR('公開中の求人が見つかりません'))
            return

        self.stdout.write(f'候補者: {len(candidates)}人, 求人: {len(jobs)}件')

        # 応募作成
        applications_created = self.create_applications(candidates, jobs, num_applications)

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ データ作成完了！\n'
            f'   応募: {applications_created}件\n'
            f'   面接: {Interview.objects.count()}件'
        ))

    def create_applications(self, candidates, jobs, count):
        """応募データを作成"""

        created_count = 0
        existing_pairs = set()

        # 各候補者が1-3件の求人に応募
        for candidate in candidates:
            num_apps = random.randint(1, min(3, len(jobs)))
            candidate_jobs = random.sample(jobs, num_apps)

            for job in candidate_jobs:
                # 重複チェック
                pair = (candidate.id, job.id)
                if pair in existing_pairs:
                    continue

                existing_pairs.add(pair)

                # 応募作成
                days_ago = random.randint(1, 60)
                applied_date = timezone.now() - timedelta(days=days_ago)

                # ステータスを決定（新しい応募ほど初期ステータスが多い）
                if days_ago < 7:
                    status = random.choice(['submitted', 'submitted', 'screening', 'screening'])
                elif days_ago < 14:
                    status = random.choice(['screening', 'screening', 'interview', 'interview'])
                elif days_ago < 30:
                    status = random.choice(['interview', 'interview', 'offer', 'rejected'])
                else:
                    status = random.choice(['offer', 'accepted', 'rejected', 'withdrawn'])

                # マッチングスコアを計算（簡易版）
                matching_score = self.calculate_simple_matching_score(candidate, job)

                # カバーレターの生成
                cover_letters = [
                    f'{job.title}のポジションに大変興味があります。私の{candidate.years_of_experience}年の経験を活かして貢献したいと考えています。',
                    f'貴社の{job.title}募集を拝見し、応募させていただきます。これまでの経験を活かし、チームに貢献できると確信しております。',
                    f'{job.title}として、これまで培ってきた技術力とチームワークを発揮したいと考えております。',
                    ''  # カバーレターなしの場合もある
                ]

                application = Application.objects.create(
                    candidate=candidate,
                    job=job,
                    status=status,
                    matching_score=matching_score,
                    cover_letter=random.choice(cover_letters)
                )

                # 応募日時を過去に設定（auto_now_addを回避するため、作成後にupdate）
                Application.objects.filter(pk=application.pk).update(applied_date=applied_date)
                application.refresh_from_db()

                created_count += 1

                # 面接が設定されている場合、面接データを作成
                if status in ['interview', 'offer', 'accepted', 'rejected']:
                    self.create_interview_for_application(application, days_ago)

        return created_count

    def calculate_simple_matching_score(self, candidate, job):
        """簡易的なマッチングスコア計算"""
        score = 50  # ベーススコア

        # スキルマッチング
        candidate_skills = set(candidate.candidate_skills.values_list('skill_id', flat=True))
        job_skills = set(job.job_skills.values_list('skill_id', flat=True))

        if job_skills:
            skill_match_rate = len(candidate_skills & job_skills) / len(job_skills)
            score += skill_match_rate * 30

        # 経験年数マッチング
        exp_level_map = {
            'entry': (0, 1),
            'junior': (1, 3),
            'mid': (3, 7),
            'senior': (7, 12),
            'lead': (10, 20)
        }

        if job.experience_level in exp_level_map:
            min_exp, max_exp = exp_level_map[job.experience_level]
            if min_exp <= candidate.years_of_experience <= max_exp:
                score += 20
            elif candidate.years_of_experience > max_exp:
                score += 10

        return min(int(score), 100)

    def create_interview_for_application(self, application, days_since_application):
        """応募に対する面接データを作成"""

        # 面接タイプ
        interview_types = ['phone', 'video', 'technical', 'hr', 'final']

        # ステータスに応じて面接数を決定
        if application.status == 'interview':
            num_interviews = random.randint(1, 2)
            possible_results = ['pending', 'passed', 'on_hold']
        elif application.status in ['offer', 'accepted']:
            num_interviews = random.randint(2, 3)
            possible_results = ['passed']
        elif application.status == 'rejected':
            num_interviews = random.randint(1, 2)
            possible_results = ['failed', 'failed', 'on_hold']
        else:
            return

        # 面接を作成
        interview_date_offset = max(1, days_since_application - random.randint(5, 20))

        for i in range(num_interviews):
            interview_date = timezone.now() - timedelta(days=interview_date_offset - i * 7)
            round_number = i + 1

            # 未来の面接の場合はpending結果
            if interview_date > timezone.now():
                result = 'pending'
            else:
                result = random.choice(possible_results)

            interview_type = interview_types[min(i, len(interview_types) - 1)]

            # 評価（完了した面接のみ）
            if result in ['passed', 'failed', 'on_hold']:
                overall_score = random.randint(3, 5) if result == 'passed' else random.randint(1, 3)
                feedback = self.generate_feedback(overall_score, interview_type)

                # 面接官の評価指標（1-5のスケール）
                technical_score = random.randint(3, 5) if interview_type == 'technical' and result == 'passed' else (random.randint(1, 3) if interview_type == 'technical' else None)
                communication_score = random.randint(3, 5) if result == 'passed' else random.randint(1, 3)
                cultural_fit_score = random.randint(3, 5) if interview_type in ['hr', 'final'] and result == 'passed' else (random.randint(1, 3) if interview_type in ['hr', 'final'] else None)

                strengths = '技術力が高い。コミュニケーション能力も良好。' if result == 'passed' else '基礎知識はある。'
                weaknesses = '特になし' if result == 'passed' else '実務経験が不足している。'
            else:
                overall_score = None
                feedback = ''
                technical_score = None
                communication_score = None
                cultural_fit_score = None
                strengths = ''
                weaknesses = ''

            Interview.objects.create(
                application=application,
                interview_type=interview_type,
                round_number=round_number,
                scheduled_date=interview_date,
                result=result,
                duration_minutes=random.choice([30, 45, 60, 90]) if result != 'pending' else 60,
                feedback=feedback,
                overall_score=overall_score,
                technical_score=technical_score,
                communication_score=communication_score,
                cultural_fit_score=cultural_fit_score,
                strengths=strengths,
                weaknesses=weaknesses,
                notes=f'{interview_type}面接の記録' if result != 'pending' else ''
            )

    def generate_feedback(self, rating, interview_type):
        """評価に基づくフィードバックを生成"""
        if rating >= 4:
            feedbacks = [
                '技術力、コミュニケーション能力ともに優れています。チームにすぐに馴染めると思います。',
                '非常に優秀な候補者です。即戦力として期待できます。',
                '技術的な知識が豊富で、説明も分かりやすかったです。',
                '前向きな姿勢と高い技術力を持っています。ぜひ採用したいです。'
            ]
        elif rating >= 3:
            feedbacks = [
                '基本的な技術力はありますが、実務経験をもう少し積む必要があります。',
                'コミュニケーション能力は高いですが、技術面で若干の不安があります。',
                '平均的な候補者です。他の候補者と比較して検討が必要です。',
                '可もなく不可もなくといった印象です。'
            ]
        else:
            feedbacks = [
                '技術力が不足しています。',
                'コミュニケーションに課題があります。',
                '求めるレベルに達していません。',
            ]

        return random.choice(feedbacks)
