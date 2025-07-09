import csv
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from election.models import (
    AcademicYear, InstitutionLevel, Institution, Position,
    Student, Election, ElectionPosition, Candidate,
    Vote, ElectionResult, Leader, Promise, PromiseUpdate,
    Rating, ElectionStatistics
)

class Command(BaseCommand):
    help = "Populate the database with complete election simulation data"

    def add_arguments(self, parser):
        parser.add_argument('--csv_file', type=str, help='Path to the CSV file containing student names')
        parser.add_argument('--students', type=int, default=1000, help='Number of students to create (default: 1000)')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        max_students = kwargs['students']
        
        self.stdout.write(self.style.SUCCESS("Starting database population..."))
        
        # 1. Create Academic Years
        self.create_academic_years()
        
        # 2. Create Institution Levels
        university_level, college_level, hostel_level = self.create_institution_levels()
        
        # 3. Create Institutions (University, Colleges, Hostels)
        udom, colleges, hostels = self.create_institutions(university_level, college_level, hostel_level)
        
        # 4. Create Positions
        positions = self.create_positions(university_level, college_level, hostel_level, udom, colleges, hostels)
        
        # 5. Create Students from CSV
        students = self.create_students_from_csv(csv_file, max_students, udom, colleges, hostels)
        
        # 6. Create Elections
        elections = self.create_elections(positions)
        
        # 7. Create Candidates (fixed to have exactly 5 per position per election)
        candidates = self.create_candidates(students, elections)
        
        # 8. Simulate Voting
        votes = self.simulate_voting(students, candidates, elections)
        
        # 9. Calculate Election Results
        self.calculate_election_results(elections, candidates)
        
        # 10. Create Leaders (fixed to have leaders for all positions in all years)
        leaders = self.create_leaders(candidates)
        
        # 11. Create Promises
        promises = self.create_promises(candidates)
        
        # 12. Create Promise Updates
        self.create_promise_updates(promises)
        
        # 13. Create Ratings
        self.create_ratings(students, leaders)
        
        # 14. Calculate Election Statistics
        self.calculate_election_statistics(elections)
        
        self.stdout.write(self.style.SUCCESS("Database successfully populated with complete election data!"))
    
    def create_academic_years(self):
        self.stdout.write("Creating academic years...")
        years = []
        
        for year in range(2020, 2025):
            name = f"{year}-{year+1}"
            start_date = datetime(year, 11, 1)
            end_date = datetime(year+1, 11, 1)
            
            # Make current year random for variety
            is_current = random.choice([True, False]) if year == 2024 else year == 2024
            
            academic_year, created = AcademicYear.objects.get_or_create(
                name=name,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_current': is_current
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created academic year: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"  Academic year {name} already exists"))
            
            years.append(academic_year)
        
        return years
    
    def create_institution_levels(self):
        self.stdout.write("Creating institution levels...")
        
        levels = [
            ('UNIVERSITY', 'University'),
            ('COLLEGE', 'College'),
            ('HOSTEL', 'Hostel'),
        ]
        
        created_levels = []
        for code, name in levels:
            level, created = InstitutionLevel.objects.get_or_create(
                level=code,
                defaults={'level': code}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created level: {name}"))
            created_levels.append(level)
        
        return created_levels
    
    def create_institutions(self, university_level, college_level, hostel_level):
        self.stdout.write("Creating institutions...")
        
        # Create University
        university, created = Institution.objects.get_or_create(
            name="University of Dodoma (UDOM)",
            level=university_level,
            defaults={'description': "The main university institution"}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"  Created university: {university.name}"))
        
        # Define colleges and their hostels
        colleges_data = {
            "College of Education (COED)": [f"Block {chr(i)}" for i in range(ord('A'), ord('T') + 1)],
            "College of Informatics and Virtual Education (CIVE)": [f"Block {i}" for i in range(1, 7)],
            "College of Earth Science (COES)": [f"Block {i}" for i in range(6, 10)],
            "College of Natural and Mathematical Sciences (CNMS)": [f"Block {i}" for i in range(10, 15)],
            "College of Business and Economics (COBE)": [f"Block {i}" for i in range(1, 20)],
            "College of Humanities and Social Sciences (CHSS)": [f"Block {i}" for i in range(1, 6)],
            "College of Health Sciences": ["Block 1", "Block 2"],
        }
        
        colleges = []
        hostels = []
        
        for college_name, hostel_names in colleges_data.items():
            college, created = Institution.objects.get_or_create(
                name=college_name,
                level=college_level,
                parent=university,
                defaults={'description': f"{college_name} at UDOM"}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created college: {college_name}"))
            colleges.append(college)
            
            for hostel_name in hostel_names:
                hostel, created = Institution.objects.get_or_create(
                    name=hostel_name,
                    level=hostel_level,
                    parent=college,
                    defaults={'description': f"Hostel {hostel_name} at {college_name}"}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"    Created hostel: {hostel_name}"))
                hostels.append(hostel)
        
        return university, colleges, hostels
    
    def create_positions(self, university_level, college_level, hostel_level, university, colleges, hostels):
        self.stdout.write("Creating positions...")
        
        positions = []
        
        # University President
        president, created = Position.objects.get_or_create(
            name="President",
            level=university_level,
            institution=university,
            defaults={'description': "University-wide president position"}
        )
        positions.append(president)
        
        # College Governors
        for college in colleges:
            governor, created = Position.objects.get_or_create(
                name=f"Governor - {college.name}",
                level=college_level,
                institution=college,
                defaults={'description': f"Governor position for {college.name}"}
            )
            positions.append(governor)
        
        # Hostel Clerks
        for hostel in hostels:
            clerk, created = Position.objects.get_or_create(
                name=f"Clerk - {hostel.name}",
                level=hostel_level,
                institution=hostel,
                defaults={'description': f"Clerk position for {hostel.name}"}
            )
            positions.append(clerk)
        
        self.stdout.write(self.style.SUCCESS(f"  Created {len(positions)} positions"))
        return positions
    
    def create_students_from_csv(self, csv_file, max_students, university, colleges, hostels):
        self.stdout.write("Creating students...")
        
        students = []
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        if not academic_year:
            academic_year = AcademicYear.objects.first()
        
        # If CSV file is provided, use it
        if csv_file:
            try:
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    students_count = 0
                    for i, row in enumerate(reader):
                        if students_count >= max_students:
                            break
                        
                        full_name = row.get('EmployeeName', '').strip()
                        if not full_name:
                            continue
                            
                        # Split name into first and last
                        name_parts = full_name.split()
                        first_name = name_parts[0] if len(name_parts) > 0 else "Unknown"
                        last_name = name_parts[-1] if len(name_parts) > 1 else "User"
                        
                        # Create user
                        username = f"{first_name.lower()}{last_name.lower()}"
                        email = f"{username}@gmail.com"
                        
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                                'password': 'password123'  # In real app, use set_password()
                            }
                        )
                        
                        # Assign to random college and hostel under that college
                        college = random.choice(colleges)
                        possible_hostels = Institution.objects.filter(level__level='HOSTEL', parent=college)
                        hostel = random.choice(list(possible_hostels)) if possible_hostels.exists() else None
                        try:
                            student, created = Student.objects.get_or_create(
                                user=user,
                                institution=hostel,
                                academic_year=academic_year,
                                is_candidate=random.choice([True, False])  # Some will be candidates later
                            )
                            students_count+=1
                            students.append(student)
                        except:
                            continue
                        
                        if len(students) % 100 == 0:
                            self.stdout.write(f"  Created {len(students)} students...")
                
                self.stdout.write(self.style.SUCCESS(f"  Created {len(students)} students from CSV"))
                return students
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f"CSV file not found at {csv_file}, falling back to generated names"))
        
        # Fallback to generated names if CSV not provided or not found
        for i in range(max_students):
            first_name = f"Student{i}"
            last_name = f"User{i}"
            username = f"student{i}"
            email = f"{username}@example.com"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'password': 'password123'
                }
            )
            
            # Assign to random college and hostel under that college
            college = random.choice(colleges)
            possible_hostels = Institution.objects.filter(level__level='HOSTEL', parent=college)
            hostel = random.choice(list(possible_hostels)) if possible_hostels.exists() else None
            
            student = Student.objects.create(
                user=user,
                institution=hostel,
                academic_year=academic_year,
                is_candidate=random.choice([True, False])
            )
            students.append(student)
        
        self.stdout.write(self.style.SUCCESS(f"  Created {len(students)} students with generated names"))
        return students
    
    def create_elections(self, positions):
        self.stdout.write("Creating elections...")
        
        elections = []
        academic_years = AcademicYear.objects.all()
        
        for year in academic_years:
            # Create elections for each level in each year
            for level in InstitutionLevel.objects.all():
                election_name = f"{year.name} {level.get_level_display()} Election"
                
                # Random dates within the academic year
                start_date = year.start_date + timedelta(days=random.randint(30, 100))
                end_date = start_date + timedelta(days=random.randint(3, 7))  # Elections last 3-7 days
                
                start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
                end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.get_current_timezone())

                election = Election.objects.create(
                    name=election_name,
                    description=f"{level.get_level_display()} election for academic year {year.name}",
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    academic_year=year,
                    level=level,
                    status=(
                        'COMPLETED' if timezone.now() > end_datetime
                        else 'ACTIVE' if start_datetime <= timezone.now() <= end_datetime
                        else 'UPCOMING'
                    )
                )
                
                # Add positions to election that match the level
                for position in positions:
                    if position.level == level:
                        ElectionPosition.objects.create(
                            election=election,
                            position=position,
                            max_candidates=5
                        )
                
                elections.append(election)
                self.stdout.write(self.style.SUCCESS(f"  Created election: {election_name}"))
        
        return elections
    
    def create_candidates(self, students, elections):
        self.stdout.write("Creating candidates...")
        
        candidates = []
        
        for election in elections:
            for election_position in election.electionposition_set.all():
                position = election_position.position
                institution = position.institution
                
                # Get eligible students (those belonging to the institution)
                if position.level.level == 'HOSTEL':
                    eligible_students = [s for s in students if s.institution == institution]
                elif position.level.level == 'COLLEGE':
                    eligible_students = [s for s in students if s.institution.parent == institution]
                else:  # UNIVERSITY
                    eligible_students = list(students)  # All students can vote for president
                
                # Select exactly 5 candidates (or less if not enough students)
                num_candidates = min(5, len(eligible_students))
                candidate_students = random.sample(eligible_students, num_candidates) if eligible_students else []
                
                for student in candidate_students:
                    # Mark student as candidate
                    student.is_candidate = True
                    student.save()
                    try:
                        candidate = Candidate.objects.create(
                            student=student,
                            election_position=election_position,
                            manifesto=f"My manifesto for {position.name} position",
                            is_approved=True
                        )
                        candidates.append(candidate)
                    except:
                        continue
            self.stdout.write(self.style.SUCCESS(f"  Created candidates for election: {election.name}"))
        
        return candidates
    
    def simulate_voting(self, students, candidates, elections):
        self.stdout.write("Simulating voting...")
        
        votes = []
        
        for election in elections:
            # Get all positions in this election
            election_positions = election.electionposition_set.all()
            
            for student in students:
                # Only some students will vote (60-90% participation)
                if random.random() > random.uniform(0.1, 0.4):
                    for election_position in election_positions:
                        position = election_position.position
                        
                        # Check if student is eligible to vote for this position
                        if position.level.level == 'HOSTEL' and student.institution != position.institution:
                            continue
                        if position.level.level == 'COLLEGE' and student.institution.parent != position.institution:
                            continue
                        
                        # Get candidates for this position
                        position_candidates = [
                            c for c in candidates 
                            if c.election_position == election_position
                        ]
                        
                        if not position_candidates:
                            continue
                        
                        # Student votes for one candidate (or skips sometimes)
                        if random.random() > 0.1:  # 10% chance to skip voting for this position
                            # Choose a candidate (with some randomness in popularity)
                            weights = [random.uniform(0.7, 1.3) for _ in position_candidates]
                            total = sum(weights)
                            weights = [w/total for w in weights]
                            candidate = random.choices(position_candidates, weights=weights)[0]
                            
                            # Random vote time during election period
                            vote_time = election.start_datetime + timedelta(
                                seconds=random.randint(
                                    0, 
                                    int((election.end_datetime - election.start_datetime).total_seconds())
                                )
                            )
                            try:
                                vote = Vote.objects.create(
                                    election=election,
                                    candidate=candidate,
                                    voter=student,
                                    timestamp=vote_time
                                )
                                votes.append(vote)
                            except:
                                continue
            
            self.stdout.write(self.style.SUCCESS(f"  Simulated votes for election: {election.name}"))
        
        return votes
    
    def calculate_election_results(self, elections, candidates):
        self.stdout.write("Calculating election results...")
        
        for election in elections:
            for election_position in election.electionposition_set.all():
                # Get all candidates for this position
                position_candidates = [
                    c for c in candidates 
                    if c.election_position == election_position
                ]
                
                # Calculate votes for each candidate
                candidates_with_votes = []
                for candidate in position_candidates:
                    vote_count = Vote.objects.filter(
                        election=election,
                        candidate=candidate
                    ).count()
                    candidates_with_votes.append((candidate, vote_count))
                
                # Sort by vote count descending
                candidates_with_votes.sort(key=lambda x: x[1], reverse=True)
                
                # Create election results
                total_votes = sum(votes for _, votes in candidates_with_votes)
                for rank, (candidate, votes) in enumerate(candidates_with_votes, start=1):
                    percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                    
                    ElectionResult.objects.create(
                        election=election,
                        candidate=candidate,
                        total_votes=votes,
                        percentage=percentage,
                        position_rank=rank,
                        is_winner=(rank == 1)
                    )
            
            self.stdout.write(self.style.SUCCESS(f"  Calculated results for election: {election.name}"))
    
    def create_leaders(self, candidates):
        self.stdout.write("Creating leaders...")
        
        leaders = []
        
        # Get all winning candidates
        winning_candidates = Candidate.objects.filter(
            electionresult__is_winner=True
        ).distinct()
        
        for candidate in winning_candidates:
            position = candidate.election_position.position
            election = candidate.election_position.election
            start_date = election.end_datetime.date()
            end_date = election.academic_year.end_date
            
            leader = Leader.objects.create(
                candidate=candidate,
                position=position,
                institution=position.institution,
                start_date=start_date,
                end_date=end_date,
                is_active=(end_date >= timezone.now().date())
            )
            leaders.append(leader)
        
        self.stdout.write(self.style.SUCCESS(f"  Created {len(leaders)} leaders"))
        return leaders
    
    def create_promises(self, candidates):
        self.stdout.write("Creating promises...")
        
        promises = []
        promise_templates = [
            "Improve student welfare",
            "Enhance academic resources",
            "Organize more social events",
            "Improve hostel facilities",
            "Increase transparency in leadership",
            "Create more study spaces",
            "Improve sports facilities",
            "Advocate for better food options",
            "Organize career guidance sessions",
            "Improve internet connectivity"
        ]
        
        for candidate in candidates:
            # Each candidate gets 3-5 promises
            num_promises = random.randint(3, 5)
            for _ in range(num_promises):
                promise_text = random.choice(promise_templates)
                promise = Promise.objects.create(
                    candidate=candidate,
                    title=promise_text[:50],
                    description=f"Detailed plan for {promise_text.lower()}"
                )
                promises.append(promise)
        
        self.stdout.write(self.style.SUCCESS(f"  Created {len(promises)} promises"))
        return promises
    
    def create_promise_updates(self, promises):
        self.stdout.write("Creating promise updates...")
        
        status_choices = ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED']
        
        for promise in promises:
            # Create initial status
            PromiseUpdate.objects.create(
                promise=promise,
                status='NOT_STARTED',
                update="Promise made during campaign"
            )
            
            # 70% chance of having updates
            if random.random() < 0.7:
                num_updates = random.randint(1, 3)
                for i in range(num_updates):
                    days_after = random.randint(30, 300)
                    update_date = promise.candidate.election_position.election.end_datetime + timedelta(days=days_after)
                    
                    # Progress through statuses
                    if i == num_updates - 1:  # Last update
                        status = random.choice(['COMPLETED', 'FAILED'])
                    else:
                        status = 'IN_PROGRESS'
                    
                    update_texts = {
                        'NOT_STARTED': "Planning phase",
                        'IN_PROGRESS': "Implementation ongoing",
                        'COMPLETED': "Successfully delivered",
                        'FAILED': "Could not deliver due to unforeseen circumstances"
                    }
                    
                    PromiseUpdate.objects.create(
                        promise=promise,
                        status=status,
                        update=update_texts[status],
                        timestamp=update_date
                    )
        
        self.stdout.write(self.style.SUCCESS("  Created promise updates"))
    
    def create_ratings(self, students, leaders):
        self.stdout.write("Creating ratings...")
        
        ratings = []
        
        for leader in leaders:
            # Get students in the same institution
            if leader.position.level.level == 'HOSTEL':
                eligible_students = [s for s in students if s.institution == leader.institution]
            elif leader.position.level.level == 'COLLEGE':
                eligible_students = [s for s in students if s.institution.parent == leader.institution]
            else:  # UNIVERSITY
                eligible_students = students  # All students can rate university president
            
            # Only some students will rate (30-60%)
            num_raters = int(len(eligible_students) * random.uniform(0.3, 0.6))
            raters = random.sample(eligible_students, num_raters) if eligible_students else []
            
            for student in raters:
                # Random rating with some bias toward middle values
                rating_value = min(5, max(1, int(random.gauss(3.5, 1))))
                
                # Random date during leadership period
                rating_date = leader.start_date + timedelta(
                    days=random.randint(0, (leader.end_date - leader.start_date).days)
                )
                try:
                    rating = Rating.objects.create(
                        leader=leader,
                        student=student,
                        score=rating_value,
                        comment=random.choice([
                            "Good job!",
                            "Could be better",
                            "Satisfactory performance",
                            "Needs improvement",
                            "Excellent leadership",
                            None, None, None  # Higher chance of no comment
                        ]),
                        timestamp=rating_date
                    )
                except:
                    continue
                ratings.append(rating)
        
        self.stdout.write(self.style.SUCCESS(f"  Created {len(ratings)} ratings"))
    
    def calculate_election_statistics(self, elections):
        self.stdout.write("Calculating election statistics...")
        
        for election in elections:
            total_voters = Student.objects.filter(
                academic_year=election.academic_year
            ).count()
            
            total_votes_cast = Vote.objects.filter(
                election=election
            ).count()
            
            voter_turnout = (total_votes_cast / total_voters * 100) if total_voters > 0 else 0
            
            leading_candidate = ElectionResult.objects.filter(
                election=election,
                is_winner=True
            ).first().candidate if ElectionResult.objects.filter(election=election).exists() else None
            
            ElectionStatistics.objects.create(
                election=election,
                total_voters=total_voters,
                total_votes_cast=total_votes_cast,
                voter_turnout=voter_turnout,
                leading_candidate=leading_candidate
            )
        
        self.stdout.write(self.style.SUCCESS("  Calculated election statistics"))