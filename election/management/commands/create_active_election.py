import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from election.models import (
    AcademicYear, InstitutionLevel, Institution, Position,
    Student, Election, ElectionPosition, Candidate,
    Vote, ElectionResult
)

class Command(BaseCommand):
    help = "Creates an active election that's 80% complete (started 8 days ago, ends in 2 days)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating active election scenario..."))
        
        # Get or create current academic year
        current_year = datetime.now().year
        academic_year, created = AcademicYear.objects.get_or_create(
            name=f"{current_year}-{current_year+1}",
            defaults={
                'start_date': datetime(current_year, 1, 1),
                'end_date': datetime(current_year+1, 1, 1),
                'is_current': True
            }
        )
        
        # Clear any existing current elections to avoid conflicts
        Election.objects.filter(status='ACTIVE').update(status='COMPLETED')
        
        # Create active election for each institution level
        university_level = InstitutionLevel.objects.get(level='UNIVERSITY')
        college_level = InstitutionLevel.objects.get(level='COLLEGE')
        hostel_level = InstitutionLevel.objects.get(level='HOSTEL')
        
        # Election dates - started 8 days ago, ends in 2 days (10 day duration)
        now = datetime.now()
        start_date = now - timedelta(days=8)
        end_date = now + timedelta(days=2)
        
        # Create elections for each level
        self.create_level_election(
            "University Wide Elections",
            university_level,
            academic_year,
            start_date,
            end_date
        )
        
        self.create_level_election(
            "College Elections",
            college_level,
            academic_year,
            start_date,
            end_date
        )
        
        self.create_level_election(
            "Hostel Elections",
            hostel_level,
            academic_year,
            start_date,
            end_date
        )
        
        self.stdout.write(self.style.SUCCESS("Active election scenario created successfully!"))
    
    def create_level_election(self, name_prefix, level, academic_year, start_date, end_date):
        """Create election for a specific level with all positions and candidates"""
        self.stdout.write(f"Creating {level.get_level_display()} election...")
        
        # Create the election
        election = Election.objects.create(
            name=f"{name_prefix} {academic_year.name}",
            description=f"{level.get_level_display()} elections for {academic_year.name}",
            start_datetime=start_date,
            end_datetime=end_date,
            academic_year=academic_year,
            level=level,
            status='ACTIVE'
        )
        
        # Get all positions for this level
        positions = Position.objects.filter(level=level)
        
        # Get all students in the current academic year
        students = Student.objects.all()
        
        for position in positions:
            # Create election position
            election_position = ElectionPosition.objects.create(
                election=election,
                position=position,
                max_candidates=5
            )
            
            # Get eligible students for this position
            if level.level == 'HOSTEL':
                eligible_students = students.filter(institution=position.institution)
            elif level.level == 'COLLEGE':
                eligible_students = students.filter(institution__parent=position.institution)
            else:  # UNIVERSITY
                eligible_students = students  # All students can run for university positions
            
            # Select 3-5 candidates randomly
            num_candidates = min(random.randint(3, 5), eligible_students.count())
            if num_candidates == 0:
                self.stdout.write(self.style.WARNING(f"No eligible students for position {position.name}"))
                continue
                
            candidate_students = random.sample(list(eligible_students), num_candidates)
            
            # Create candidates
            for student in candidate_students:
                student.is_candidate = True
                student.save()
                Candidate.objects.create(
                    student=student,
                    election_position=election_position,
                    manifesto=f"My plan for {position.name} position",
                    is_approved=True
                )
            
            self.stdout.write(f"  Created {num_candidates} candidates for {position.name}")
            
            # Simulate votes (80% of eligible voters have voted)
            self.simulate_votes(election, position, election_position, academic_year)
        
        self.stdout.write(self.style.SUCCESS(f"Created {level.get_level_display()} election with {positions.count()} positions"))
    
    def simulate_votes(self, election, position, election_position, academic_year):
        """Simulate votes for this position (80% of eligible voters)"""
        # Get eligible voters
        if position.level.level == 'HOSTEL':
            voters = Student.objects.filter(
                academic_year=academic_year,
                institution=position.institution
            )
        elif position.level.level == 'COLLEGE':
            voters = Student.objects.filter(
                academic_year=academic_year,
                institution__parent=position.institution
            )
        else:  # UNIVERSITY
            voters = Student.objects.filter(academic_year=academic_year)
        
        candidates = list(election_position.candidate_set.all())
        if not candidates:
            return
            
        num_voters = voters.count()
        if num_voters == 0:
            return
            
        # We want 80% participation
        target_votes = int(num_voters * 0.8)
        existing_votes = Vote.objects.filter(
            election=election,
            candidate__election_position=election_position
        ).count()
        
        votes_needed = max(0, target_votes - existing_votes)
        
        # Create weights for candidates (some randomness in popularity)
        weights = [random.uniform(0.7, 1.3) for _ in candidates]
        total = sum(weights)
        weights = [w/total for w in weights]
        
        # Create votes
        for i in range(votes_needed):
            # Random voter who hasn't voted for this position yet
            voter = random.choice(voters)
            while Vote.objects.filter(
                election=election,
                voter=voter,
                candidate__election_position=election_position
            ).exists():
                voter = random.choice(voters)
            
            # Choose candidate based on weights
            candidate = random.choices(candidates, weights=weights)[0]
            
            # Random vote time between start date and now (80% complete)
            vote_time = election.start_datetime + (
                (datetime.now() - election.start_datetime) * random.uniform(0, 0.8)
            )
            
            Vote.objects.create(
                election=election,
                candidate=candidate,
                voter=voter,
                timestamp=vote_time
            )
        
        self.stdout.write(f"    Simulated {votes_needed} votes for {position.name}")