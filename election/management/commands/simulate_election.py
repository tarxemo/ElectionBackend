import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
# from django.utils import datetime
from django.contrib.auth.models import User
from django.db import transaction
from faker import Faker
from ...models import (
    AcademicYear, InstitutionLevel, Institution, Position, Student,
    Election, ElectionPosition, Candidate, Vote, ElectionResult,
    ElectionStatistics
)
from django.db.models import Count

fake = Faker()

class Command(BaseCommand):
    help = 'Simulates an election with historical data and real-time voting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--election-id',
            type=int,
            help='ID of the election to simulate (will create one if not provided)',
        )
        parser.add_argument(
            '--speed',
            type=float,
            default=1.0,
            help='Speed multiplier for real-time simulation (1.0 = real time)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Total duration of election in days',
        )
        parser.add_argument(
            '--voters',
            type=int,
            default=100,
            help='Approximate number of voters to simulate',
        )

    def handle(self, *args, **options):
        self.election_id = options['election_id']
        self.speed = options['speed']
        self.total_days = options['days']
        self.target_voters = options['voters']
        
        # Calculate time parameters
        self.now = datetime.now()
        self.election_end = self.now + timedelta(days=self.total_days)
        
        if self.election_id:
            try:
                self.election = Election.objects.get(pk=self.election_id)
                self.stdout.write(self.style.SUCCESS(f'Using existing election: {self.election}'))
            except Election.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Election with ID {self.election_id} not found'))
                return
        else:
            self.create_election()
        
        # Simulate historical data (first 5 days)
        if self.election.start_datetime < self.now:
            self.simulate_historical_voting()
        
        # Start real-time simulation if election is still active
        if self.election.status == 'ACTIVE':
            self.stdout.write(self.style.SUCCESS('Starting real-time voting simulation...'))
            self.simulate_realtime_voting()
        else:
            self.stdout.write(self.style.WARNING('Election is not active - no real-time simulation'))

    def create_election(self):
        """Create a new election if one wasn't provided"""
        self.stdout.write('Creating new election...')
        
        # Get or create required models
        academic_year, _ = AcademicYear.objects.get_or_create(
            name=f"{self.now.year}-{self.now.year+1}",
            defaults={
                'start_date': datetime(self.now.year, 1, 1),
                'end_date': datetime(self.now.year+1, 12, 31),
                'is_current': True
            }
        )
        
        # Create university level and institution
        university_level, _ = InstitutionLevel.objects.get_or_create(
            level='UNIVERSITY',
            defaults={'level': 'UNIVERSITY'}
        )
        
        university, _ = Institution.objects.get_or_create(
            name="Example University",
            level=university_level,
            defaults={'description': "Main university institution"}
        )
        
        # Create some positions
        positions = []
        for title in ["President", "Vice President", "Secretary"]:
            pos, _ = Position.objects.get_or_create(
                name=title,
                level=university_level,
                institution=university,
                defaults={'voting_power': 1}
            )
            positions.append(pos)
        
        # Create the election
        self.election = Election.objects.create(
            name="Annual Student Election",
            description="Simulated election for demonstration purposes",
            status='ACTIVE',
            start_datetime=self.now - timedelta(days=5),
            end_datetime=self.now + timedelta(days=2),  # 7 day total duration
            academic_year=academic_year,
            level=university_level,
            institution=university
        )
        
        # Add positions to election
        for position in positions:
            ElectionPosition.objects.create(
                election=self.election,
                position=position,
                max_candidates=3
            )
        
        # Create candidates
        self.create_candidates()
        
        self.stdout.write(self.style.SUCCESS(f'Created new election: {self.election}'))

    def create_candidates(self):
        """Create candidate students for the election"""
        # Get all election positions
        election_positions = ElectionPosition.objects.filter(election=self.election)
        
        # Create some fake students
        for i in range(10):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=f'student{i}@example.com',
                password='password'
            )
            
            student, created = Student.objects.get_or_create(
                user=user,
                institution=self.election.institution,
                academic_year=self.election.academic_year,
                is_active=True
            )
            
            # Make some students candidates
            if i < 6:  # First 6 students are candidates
                for position in random.sample(
                    list(election_positions), 
                    random.randint(1, min(2, len(election_positions)))
                ):
                    Candidate.objects.create(
                        student=student,
                        election_position=position,
                        manifesto=fake.paragraph(),
                        is_approved=True,
                        approved_at=datetime.now() - timedelta(days=1)
                    )

    def simulate_historical_voting(self):
        """Simulate voting data for the first 5 days"""
        self.stdout.write('Simulating historical voting data...')
        
        # Get all eligible voters and candidates
        voters = Student.objects.filter(
            institution=self.election.institution,
            academic_year=self.election.academic_year,
            is_active=True
        )
        
        candidates = Candidate.objects.filter(
            election_position__election=self.election,
            is_approved=True
        ).select_related('election_position')
        
        if not candidates.exists():
            self.stdout.write(self.style.ERROR('No approved candidates found for this election'))
            return
        
        # Calculate voting parameters
        total_voters = min(self.target_voters, voters.count())
        days_passed = (self.now - self.election.start_datetime).days
        votes_per_day = total_voters // self.total_days
        
        self.stdout.write(f'Simulating {days_passed} days of voting ({votes_per_day * days_passed} votes)...')
        
        # Simulate voting for each historical day
        for day in range(days_passed):
            day_date = self.election.start_datetime + timedelta(days=day)
            
            # Simulate daily voting pattern (more active during certain hours)
            for hour in range(8, 20):  # 8am to 8pm
                hour_votes = random.randint(0, votes_per_day // 12)
                
                for _ in range(hour_votes):
                    # Select a random voter who hasn't voted yet today
                    voter = random.choice(voters)
                    
                    # Get all positions they can vote for
                    positions = ElectionPosition.objects.filter(
                        election=self.election,
                        position__institution__in=self.get_voting_institutions(voter)
                    )
                    
                    # Create votes for each position
                    for position in positions:
                        position_candidates = [
                            c for c in candidates 
                            if c.election_position == position
                        ]
                        
                        if position_candidates:
                            candidate = random.choice(position_candidates)
                            vote_time = day_date + timedelta(
                                hours=hour,
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59)
                            )
                            
                            Vote.objects.create(
                                election=self.election,
                                candidate=candidate,
                                voter=voter,
                                timestamp=vote_time,
                                weight=1
                            )
        
        self.stdout.write(self.style.SUCCESS('Historical voting simulation complete'))

    def get_voting_institutions(self, student):
        """Get all institutions a student can vote in (including parents)"""
        institutions = [student.institution]
        current = student.institution
        
        # Walk up the parent hierarchy
        while current.parent:
            institutions.append(current.parent)
            current = current.parent
        
        return institutions

    def simulate_realtime_voting(self):
        """Simulate real-time voting until election ends"""
        from time import sleep
        
        # Get all eligible voters and candidates
        voters = list(Student.objects.filter(
            institution=self.election.institution,
            academic_year=self.election.academic_year,
            is_active=True
        ))
        
        candidates = list(Candidate.objects.filter(
            election_position__election=self.election,
            is_approved=True
        ).select_related('election_position'))
        
        # Get voters who haven't voted yet
        voters_who_voted = set(
            Vote.objects.filter(election=self.election)
            .values_list('voter_id', flat=True)
            .distinct()
        )
        
        remaining_voters = [v for v in voters if v.id not in voters_who_voted]
        total_remaining = len(remaining_voters)
        
        self.stdout.write(f'Starting real-time simulation with {total_remaining} remaining voters...')
        
        try:
            while datetime.now() < self.election.end_datetime and remaining_voters:
                # Calculate time until next vote (inversely proportional to remaining time)
                time_left = (self.election.end_datetime - datetime.now()).total_seconds()
                avg_wait = (time_left / max(1, len(remaining_voters))) / self.speed
                
                # Randomize wait time around the average
                wait_time = max(0, random.normalvariate(avg_wait, avg_wait/2))
                sleep(wait_time)
                
                # Select a random voter and create their votes
                voter = random.choice(remaining_voters)
                remaining_voters.remove(voter)
                
                positions = ElectionPosition.objects.filter(
                    election=self.election,
                    position__institution__in=self.get_voting_institutions(voter)
                )
                
                # Create votes for each position
                for position in positions:
                    position_candidates = [
                        c for c in candidates 
                        if c.election_position_id == position.id
                    ]
                    
                    if position_candidates:
                        candidate = random.choice(position_candidates)
                        Vote.objects.create(
                            election=self.election,
                            candidate=candidate,
                            voter=voter,
                            timestamp=datetime.now(),
                            weight=1
                        )
                
                # Update election statistics periodically
                if random.random() < 0.1:  # 10% chance to update stats
                    self.update_election_statistics()
                
                self.stdout.write(f'Vote recorded for {voter.user.get_full_name()} ({len(remaining_voters)} remaining)')
        
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Simulation interrupted by user'))
        
        # Final statistics update
        self.update_election_statistics()
        self.stdout.write(self.style.SUCCESS('Election simulation complete'))

    def update_election_statistics(self):
        """Calculate and update election statistics"""
        with transaction.atomic():
            # Calculate total voters and votes
            total_voters = Student.objects.filter(
                institution=self.election.institution,
                academic_year=self.election.academic_year,
                is_active=True
            ).count()
            
            total_votes = Vote.objects.filter(election=self.election).count()
            
            # Calculate voter turnout
            turnout = (total_votes / total_voters * 100) if total_voters > 0 else 0
            
            # Get leading candidate
            results = Vote.objects.filter(election=self.election)\
                .values('candidate')\
                .annotate(vote_count=Count('id'))\
                .order_by('-vote_count')
            
            leading_candidate = None
            if results:
                leading_candidate_id = results[0]['candidate']
                leading_candidate = Candidate.objects.get(pk=leading_candidate_id)
            
            # Update or create statistics
            ElectionStatistics.objects.update_or_create(
                election=self.election,
                defaults={
                    'total_voters': total_voters,
                    'total_votes_cast': total_votes,
                    'voter_turnout': turnout,
                    'leading_candidate': leading_candidate
                }
            )
            
            # Update election results for each candidate
            for candidate in Candidate.objects.filter(election_position__election=self.election):
                total_votes = Vote.objects.filter(candidate=candidate).count()
                percentage = (total_votes / total_votes * 100) if total_votes > 0 else 0
                
                ElectionResult.objects.update_or_create(
                    election=self.election,
                    candidate=candidate,
                    defaults={
                        'total_votes': total_votes,
                        'percentage': percentage,
                        'is_winner': False  # Will be set after election ends
                    }
                )