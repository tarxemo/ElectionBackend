import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from election.models import (
    Election, Institution, Position, Student, 
    ElectionPosition, Candidate, Vote
)

class Command(BaseCommand):
    help = "Simulates real-time election voting with customizable parameters"

    def add_arguments(self, parser):
        parser.add_argument(
            '--election_name', 
            type=str, 
            required=True,
            help='Name of the election to create or simulate'
        )
        parser.add_argument(
            '--days', 
            type=int, 
            default=7,
            help='Duration of election in days (1-10)'
        )
        parser.add_argument(
            '--voter_turnout', 
            type=float, 
            default=0.7,
            help='Expected voter turnout ratio (0.1 to 1.0)'
        )
        parser.add_argument(
            '--daily_variation', 
            type=float, 
            default=0.2,
            help='Daily voting pattern variation (0.1 to 0.5)'
        )
        parser.add_argument(
            '--peak_day', 
            type=int, 
            default=None,
            help='Specific day when voting peaks (1 to days)'
        )
        parser.add_argument(
            '--force_new', 
            action='store_true',
            help='Force creation of new election even if name exists'
        )

    def handle(self, *args, **kwargs):
        election_name = kwargs['election_name']
        duration_days = min(max(kwargs['days'], 1), 10)  # Clamp between 1-10 days
        voter_turnout = min(max(kwargs['voter_turnout'], 0.1), 1.0)
        daily_variation = min(max(kwargs['daily_variation'], 0.1), 0.5)
        peak_day = kwargs['peak_day']
        force_new = kwargs['force_new']

        # 1. Setup or get existing election
        election = self.setup_election(election_name, duration_days, force_new)
        if not election:
            return

        # 2. Determine current election day (if in progress)
        current_day = self.get_current_election_day(election, duration_days)

        # 3. Get or create positions and candidates
        positions = self.get_or_create_positions(election)
        candidates = self.get_or_create_candidates(election, positions)

        # 4. Simulate voting for current day
        self.simulate_voting(
            election, 
            candidates, 
            current_day,
            duration_days,
            voter_turnout,
            daily_variation,
            peak_day
        )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully simulated voting for day {current_day} of {election.name}"
        ))

    def setup_election(self, name, duration_days, force_new):
        """Create new election or get existing one"""
        if not force_new:
            try:
                election = Election.objects.get(name=name)
                self.stdout.write(self.style.SUCCESS(
                    f"Found existing election: {name} (ID: {election.id})"
                ))
                return election
            except Election.DoesNotExist:
                pass

        # Create new election
        start_date = timezone.now().replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        end_date = start_date + timedelta(days=duration_days)

        election = Election.objects.create(
            name=name,
            description=f"Simulated election running for {duration_days} days",
            start_datetime=start_date,
            end_datetime=end_date,
            status='ACTIVE' if start_date <= timezone.now() <= end_date else (
                'COMPLETED' if timezone.now() > end_date else 'UPCOMING'
            ),
            academic_year=AcademicYear.objects.filter(is_current=True).first()
        )

        self.stdout.write(self.style.SUCCESS(
            f"Created new election: {name} running from {start_date} to {end_date}"
        ))
        return election

    def get_current_election_day(self, election, duration_days):
        """Determine which day of the election we're simulating"""
        if timezone.now() < election.start_datetime:
            return 1  # First day if not started yet
        
        if timezone.now() > election.end_datetime:
            return duration_days  # Last day if already ended

        elapsed = timezone.now() - election.start_datetime
        current_day = min(elapsed.days + 1, duration_days)
        
        # Add some randomness to simulate different times of day
        if random.random() < 0.3:
            current_day = min(current_day + 1, duration_days)
        elif random.random() < 0.2:
            current_day = max(current_day - 1, 1)
            
        return current_day

    def get_or_create_positions(self, election):
        """Get or create positions for the election"""
        positions = []
        
        # University level positions
        university = Institution.objects.filter(level__level='UNIVERSITY').first()
        if university:
            positions.append(self.get_or_create_position(
                election, university, "President"
            ))
        
        # College level positions
        colleges = Institution.objects.filter(level__level='COLLEGE')
        for college in colleges:
            positions.append(self.get_or_create_position(
                election, college, "Governor"
            ))
        
        # Hostel level positions
        hostels = Institution.objects.filter(level__level='HOSTEL')
        for hostel in hostels:
            positions.append(self.get_or_create_position(
                election, hostel, "Clerk"
            ))
        
        return positions

    def get_or_create_position(self, election, institution, title):
        """Get or create a specific position"""
        position, created = Position.objects.get_or_create(
            name=f"{title} - {institution.name}",
            institution=institution,
            level=institution.level,
            defaults={'description': f"{title} position for {institution.name}"}
        )
        
        # Create election position if needed
        ElectionPosition.objects.get_or_create(
            election=election,
            position=position,
            defaults={'max_candidates': 5}
        )
        
        return position

    def get_or_create_candidates(self, election, positions):
        """Get or create candidates for each position"""
        candidates = []
        
        for position in positions:
            # Get existing candidates for this position
            existing_candidates = Candidate.objects.filter(
                election_position__election=election,
                election_position__position=position
            )
            
            if existing_candidates.exists():
                candidates.extend(existing_candidates)
                continue
                
            # Create new candidates if none exist
            institution = position.institution
            eligible_students = self.get_eligible_students(institution)
            
            # Select 3-5 candidates (with some randomness)
            num_candidates = random.randint(3, min(5, len(eligible_students)))
            selected_students = random.sample(eligible_students, num_candidates)
            
            for student in selected_students:
                election_position = ElectionPosition.objects.get(
                    election=election,
                    position=position
                )
                
                candidate = Candidate.objects.create(
                    student=student,
                    election_position=election_position,
                    manifesto=f"My plan as {position.name}",
                    is_approved=True
                )
                candidates.append(candidate)
                student.is_candidate = True
                student.save()
        
        return candidates

    def get_eligible_students(self, institution):
        """Get students eligible to run for a position"""
        if institution.level.level == 'UNIVERSITY':
            return list(Student.objects.filter(
                institution__level__level='HOSTEL'
            ).order_by('?')[:100])  # Limit to 100 random students for performance
        
        elif institution.level.level == 'COLLEGE':
            return list(Student.objects.filter(
                institution__parent=institution
            ).order_by('?')[:50])
        
        else:  # HOSTEL
            return list(Student.objects.filter(
                institution=institution
            ).order_by('?')[:20])

    def simulate_voting(self, election, candidates, current_day, 
                      total_days, turnout, daily_variation, peak_day):
        """Simulate realistic voting patterns"""
        self.stdout.write(f"Simulating voting for day {current_day}...")
        
        # Calculate daily voting distribution
        daily_distribution = self.calculate_daily_distribution(
            total_days, 
            daily_variation, 
            peak_day
        )
        
        # Get all eligible voters
        voters = self.get_eligible_voters(election)
        total_voters = len(voters)
        votes_to_cast = int(total_voters * turnout * daily_distribution[current_day-1])
        
        self.stdout.write(f"Simulating {votes_to_cast} votes for day {current_day}")
        
        # Group candidates by position for efficient voting
        candidates_by_position = {}
        for candidate in candidates:
            pos_id = candidate.election_position.position.id
            if pos_id not in candidates_by_position:
                candidates_by_position[pos_id] = []
            candidates_by_position[pos_id].append(candidate)
        
        # Simulate votes
        votes_created = 0
        vote_objects = []
        
        for _ in range(votes_to_cast):
            voter = random.choice(voters)
            
            # Voter can vote for each position they're eligible for
            for pos_id, pos_candidates in candidates_by_position.items():
                position = pos_candidates[0].election_position.position
                
                # Check voter eligibility for this position
                if not self.is_voter_eligible(voter, position):
                    continue
                
                # Simulate some voters skipping certain positions
                if random.random() < 0.1:  # 10% chance to skip
                    continue
                
                # Weight candidates based on some factors (simulating popularity)
                weights = self.calculate_candidate_weights(pos_candidates)
                candidate = random.choices(pos_candidates, weights=weights)[0]
                
                # Create vote with realistic timestamp during the day
                vote_time = self.generate_vote_timestamp(election, current_day)
                
                vote_objects.append(Vote(
                    election=election,
                    candidate=candidate,
                    voter=voter,
                    timestamp=vote_time
                ))
                
                votes_created += 1
                
                # Bulk create in batches for performance
                if len(vote_objects) >= 1000:
                    Vote.objects.bulk_create(vote_objects)
                    vote_objects = []
        
        # Create remaining votes
        if vote_objects:
            Vote.objects.bulk_create(vote_objects)
        
        self.stdout.write(self.style.SUCCESS(
            f"Created {votes_created} votes for day {current_day}"
        ))

    def calculate_daily_distribution(self, total_days, variation, peak_day=None):
        """Calculate realistic daily voting distribution"""
        if not peak_day:
            peak_day = random.randint(2, total_days-1) if total_days > 2 else 1
        
        # Base distribution (normal distribution around peak day)
        days = list(range(1, total_days+1))
        distribution = [
            self.normal_pdf(day, peak_day, variation*2) 
            for day in days
        ]
        
        # Normalize to sum to 1
        total = sum(distribution)
        return [x/total for x in distribution]

    def normal_pdf(self, x, mean, stddev):
        """Normal distribution probability density function"""
        return (1.0 / (stddev * ((2 * 3.1415926535) ** 0.5))) * \
               (2.7182818284 ** (-((x - mean) ** 2) / (2 * stddev ** 2)))

    def get_eligible_voters(self, election):
        """Get all students eligible to vote in this election"""
        return list(Student.objects.filter(
            academic_year=election.academic_year
        ).order_by('?')[:10000])  # Limit for performance

    def is_voter_eligible(self, voter, position):
        """Check if voter is eligible to vote for a position"""
        if position.level.level == 'UNIVERSITY':
            return True
        elif position.level.level == 'COLLEGE':
            return voter.institution.parent == position.institution
        else:  # HOSTEL
            return voter.institution == position.institution

    def calculate_candidate_weights(self, candidates):
        """Calculate weights for candidates (simulating popularity)"""
        weights = []
        base_popularity = {
            'incumbent': 1.5,
            'active': 1.2,
            'new': 1.0
        }
        
        for candidate in candidates:
            # Existing candidates get popularity boost from previous votes
            existing_votes = Vote.objects.filter(candidate=candidate).count()
            
            if existing_votes > 10:
                weight = base_popularity['incumbent'] * (1 + existing_votes/100)
            elif existing_votes > 0:
                weight = base_popularity['active'] * (1 + existing_votes/50)
            else:
                weight = base_popularity['new'] * random.uniform(0.8, 1.2)
            
            weights.append(weight)
        
        return weights

    def generate_vote_timestamp(self, election, current_day):
        """Generate realistic vote timestamp within the specified day"""
        day_start = election.start_datetime + timedelta(days=current_day-1)
        day_end = day_start + timedelta(days=1)
        
        # Voting hours (8am to 6pm)
        voting_start = day_start.replace(hour=8, minute=0, second=0)
        voting_end = day_start.replace(hour=18, minute=0, second=0)
        
        # Generate random time during voting hours with peak around midday
        seconds_in_day = (voting_end - voting_start).total_seconds()
        peak_time = voting_start + timedelta(hours=5)  # 1pm peak
        
        # Normal distribution around peak time (sigma = 2 hours)
        vote_time = peak_time + timedelta(
            seconds=random.gauss(0, 2*3600)
        )
        
        # Clamp to voting hours
        vote_time = max(vote_time, voting_start)
        vote_time = min(vote_time, voting_end)
        
        return vote_time