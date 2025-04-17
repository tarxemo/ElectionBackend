import csv
import os
import random
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from election.models import Student, Hostel, University

def import_students_from_csv(request):
    """ Reads 'Salaries.csv' directly from the 'election' app and creates Student users. """
    
    # Construct the file path
    csv_path = os.path.join(settings.BASE_DIR, "election", "Salaries.csv")

    # Check if file exists
    if not os.path.exists(csv_path):
        return JsonResponse({"error": "CSV file not found."})

    students_created = 0
    errors = []

    # Read the CSV file
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                full_name = row.get("EmployeeName", "").strip()
                if not full_name:
                    continue

                name_parts = full_name.split()
                if len(name_parts) < 2:
                    errors.append(f"Invalid name format: {full_name}")
                    continue

                first_name = name_parts[0].capitalize()
                last_name = name_parts[-1].capitalize()
                username = f"{first_name.lower()}{last_name.lower()}"
                email = f"{username}@gmail.com"
                password = last_name.lower()

                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    errors.append(f"User {username} already exists.")
                    continue

                # Create User
                user = User.objects.create_user(
                    username=username, email=email, password=password,
                    first_name=first_name, last_name=last_name
                )
                user.save()
                # Randomly assign a hostel
                hostels = list(Hostel.objects.all())
                if not hostels:
                    errors.append("No hostels available.")
                    continue

                hostel = random.choice(hostels)
                college = hostel.college
                university = college.university

                # Create Student
                student = Student.objects.create(
                    user=user,
                    hostel=hostel,
                    college=college,
                    university=university
                )
                student.save()
                students_created += 1

            except Exception as e:
                errors.append(str(e))

    return JsonResponse({
        "message": f"{students_created} students created successfully.",
        "errors": errors
    })

import random
from django.http import JsonResponse
from election.models import Student, Position, Candidate

def select_candidates(request):
    """
    Selects five random students as competitors for each position based on level.
    """
    positions = Position.objects.all()
    candidates_created = 0
    errors = []

    for position in positions:
        try:
            if position.level == "HOSTEL":
                # Get all hostels
                hostels = Student.objects.values_list("hostel", flat=True).distinct()
                for hostel_id in hostels:
                    students = list(Student.objects.filter(hostel_id=hostel_id))
                    if len(students) < 5:
                        errors.append(f"Not enough students in hostel {hostel_id}.")
                        continue

                    selected_students = random.sample(students, 5)
                    for student in selected_students:
                        Candidate.objects.get_or_create(student=student, position=position)
                        candidates_created += 1

            elif position.level == "COLLEGE":
                # Get all colleges
                colleges = Student.objects.values_list("college", flat=True).distinct()
                for college_id in colleges:
                    students = list(Student.objects.filter(college_id=college_id))
                    if len(students) < 5:
                        errors.append(f"Not enough students in college {college_id}.")
                        continue

                    selected_students = random.sample(students, 5)
                    for student in selected_students:
                        Candidate.objects.get_or_create(student=student, position=position)
                        candidates_created += 1

            elif position.level == "UNIVERSITY":
                # Get all university students
                students = list(Student.objects.all())
                if len(students) < 5:
                    errors.append("Not enough students in the university.")
                    continue

                selected_students = random.sample(students, 5)
                for student in selected_students:
                    Candidate.objects.get_or_create(student=student, position=position)
                    candidates_created += 1

        except Exception as e:
            errors.append(str(e))

    return JsonResponse({
        "message": f"{candidates_created} candidates selected successfully.",
        "errors": errors
    })


import random
from django.http import JsonResponse
from django.db.models import Count
from election.models import Student, Election, Candidate, Vote

def random_voting(request):
    """
    Simulates random voting where 90% of students participate.
    Students can only vote for candidates in their own hostel, college, or university.
    """
    total_students = Student.objects.count()
    students_who_vote = random.sample(list(Student.objects.all()), int(total_students * 0.9))  # 90% participation
    votes_cast = 0
    errors = []

    for student in students_who_vote:
        try:
            # Get elections at different levels
            elections = Election.objects.all()

            for election in elections:
                # Filter candidates based on election level
                if election.level == "HOSTEL":
                    candidates = Candidate.objects.filter(position__level="HOSTEL", student__hostel=student.hostel)
                elif election.level == "COLLEGE":
                    candidates = Candidate.objects.filter(position__level="COLLEGE", student__college=student.college)
                elif election.level == "UNIVERSITY":
                    candidates = Candidate.objects.filter(position__level="UNIVERSITY", student__university=student.university)
                else:
                    continue  # Skip if level is not recognized

                # Vote for a random candidate if there are candidates in this category
                if candidates.exists():
                    chosen_candidate = random.choice(candidates)
                    Vote.objects.create(student=student, candidate=chosen_candidate, election=election)
                    votes_cast += 1

        except Exception as e:
            errors.append(str(e))

    return JsonResponse({
        "message": f"{votes_cast} votes cast successfully.",
        "non_voters": total_students - len(students_who_vote),
        "errors": errors
    })


import random
from django.http import JsonResponse
from django.db.models import Count
from election.models import Student, Candidate, LeaderRating, Vote, Position

def get_elected_leaders():
    """
    Determines the winners of each position based on the highest votes.
    Returns a dictionary of elected leaders mapped to their position level.
    """
    elected_leaders = {}

    # Get all positions (hostel, college, and university levels)
    positions = Position.objects.all()

    for position in positions:
        # Get candidates for this position and count votes
        candidates = Candidate.objects.filter(position=position).annotate(vote_count=Count('votes')).order_by('-vote_count')

        if candidates.exists():
            winner = candidates.first()  # Candidate with the most votes
            if winner.vote_count > 0:  # Ensure the candidate received votes
                elected_leaders[winner] = position.level

    return elected_leaders

def random_leader_ratings(request):
    """
    Simulates random leader ratings where only 60% of students participate.
    Students can only rate elected leaders within their hostel, college, or university.
    """
    total_students = Student.objects.count()
    students_who_rate = random.sample(list(Student.objects.all()), int(total_students * 0.6))  # 60% participation
    elected_leaders = get_elected_leaders()  # Get the actual elected leaders
    ratings_cast = 0
    errors = []

    for student in students_who_rate:
        try:
            # Get elected leaders relevant to the student's level
            hostel_leaders = [leader for leader, level in elected_leaders.items() if level == "HOSTEL" and leader.student.hostel == student.hostel]
            college_leaders = [leader for leader, level in elected_leaders.items() if level == "COLLEGE" and leader.student.college == student.college]
            university_leaders = [leader for leader, level in elected_leaders.items() if level == "UNIVERSITY" and leader.student.university == student.university]

            # Combine all relevant leaders
            leaders_to_rate = hostel_leaders + college_leaders + university_leaders

            # Rate a random selection of leaders (1 to 3)
            for leader in random.sample(leaders_to_rate, min(len(leaders_to_rate), random.randint(1, 3))):
                rating_value = random.randint(2, 5)  # Ratings from 2 to 5
                LeaderRating.objects.create(
                    leader=leader,
                    student=student,
                    rating=rating_value,
                    comment="Automated rating for elected leader."
                )
                ratings_cast += 1

        except Exception as e:
            errors.append(str(e))

    return JsonResponse({
        "message": f"{ratings_cast} ratings cast successfully.",
        "non_raters": total_students - len(students_who_rate),
        "errors": errors
    })


import random
from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse
from election.models import Vote

def randomize_vote_timestamps(request):
    """
    Randomly updates the timestamp of all votes within the last 10 days.
    """
    votes = Vote.objects.all()
    
    if not votes.exists():
        return JsonResponse({"message": "No votes found"}, status=404)

    # Get the current time
    current_time = now()

    for vote in votes:
        # Generate a random timestamp within the last 10 days
        random_days = random.randint(0, 9)  # Random day within last 10 days
        random_seconds = random.randint(0, 86400)  # Random time within the day (0 to 24 hours)
        new_timestamp = current_time - timedelta(days=random_days, seconds=random_seconds)
        
        # Update vote timestamp
        vote.timestamp = new_timestamp
        vote.save()

    return JsonResponse({"message": f"Updated {votes.count()} votes with random timestamps"})
