import graphene
from graphene import ObjectType, DateTime, Decimal, ID
from .models import Student, Vote, Candidate, Election, LeaderRating, LeaderPromise, PromiseImplementation
from .outputs import StudentOutput, VoteOutput, CandidateOutput, LeaderRatingOutput, LeaderPromiseOutput, PromiseImplementationOutput
from django.db.models import Count, F, Q
from datetime import datetime, timedelta

# Query to retrieve all students
class Query(ObjectType):
    # Query to retrieve all students
    all_students = graphene.List(StudentOutput)

    def resolve_all_students(self, info):
        return Student.objects.all()

    # Query to retrieve voting rate over time for a specific hostel, college, or university
    voting_rate_over_time = graphene.List(
        graphene.JSONString,
        level=graphene.String(required=True),
        level_id=graphene.ID(required=True),
        start_date=DateTime(required=True),
        end_date=DateTime(required=True),
    )

    def resolve_voting_rate_over_time(self, info, level, level_id, start_date, end_date):
        # Determine the level (hostel, college, or university)
        if level == "HOSTEL":
            votes = Vote.objects.filter(student__hostel_id=level_id, timestamp__range=(start_date, end_date))
        elif level == "COLLEGE":
            votes = Vote.objects.filter(student__college_id=level_id, timestamp__range=(start_date, end_date))
        elif level == "UNIVERSITY":
            votes = Vote.objects.filter(student__university_id=level_id, timestamp__range=(start_date, end_date))
        else:
            raise ValueError("Invalid level. Must be 'HOSTEL', 'COLLEGE', or 'UNIVERSITY'.")

        # Group votes by time interval (e.g., daily)
        voting_data = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            vote_count = votes.filter(timestamp__range=(current_date, next_date)).count()
            voting_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "vote_count": vote_count,
            })
            current_date = next_date

        return voting_data

    voting_rate_for_leader = graphene.List(
        graphene.JSONString,
        leader_id=graphene.ID(required=True),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
    )

    def resolve_voting_rate_for_leader(self, info, leader_id, start_date=None, end_date=None):
        # Retrieve votes for the specified leader
        votes = Vote.objects.filter(candidate_id=leader_id)

        # If no start_date and end_date are provided, use the full range
        if start_date is None or end_date is None:
            first_vote = votes.order_by("timestamp").first()
            last_vote = votes.order_by("-timestamp").first()
            
            if first_vote and last_vote:
                start_date = first_vote.timestamp
                end_date = last_vote.timestamp
            else:
                # No votes exist for this leader
                return []

        # Filter votes within the determined range
        votes = votes.filter(timestamp__range=(start_date, end_date))

        # Group votes by day
        voting_data = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            vote_count = votes.filter(timestamp__range=(current_date, next_date)).count()
            voting_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "vote_count": vote_count,
            })
            current_date = next_date

        return voting_data

    # Query to retrieve votes count for leaders competing for the same position
    votes_count_for_position = graphene.List(
        graphene.JSONString,
        position_id=graphene.ID(required=True),
    )

    def resolve_votes_count_for_position(self, info, position_id):
        candidates = Candidate.objects.filter(position_id=position_id)
        vote_counts = []
        for candidate in candidates:
            vote_count = Vote.objects.filter(candidate_id=candidate.id).count()
            vote_counts.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.student.user.get_full_name(),
                "vote_count": vote_count,
            })
        return vote_counts

    # Query to retrieve leader performance metrics (ratings and promise implementation)
    leader_performance_metrics = graphene.Field(
        graphene.JSONString,
        leader_id=graphene.ID(required=True),
    )

    def resolve_leader_performance_metrics(self, info, leader_id):
        # Retrieve leader ratings
        ratings = LeaderRating.objects.filter(leader_id=leader_id)
        average_rating = ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']

        # Retrieve promise implementation status
        promises = LeaderPromise.objects.filter(candidate_id=leader_id)
        promise_data = []
        for promise in promises:
            implementation = PromiseImplementation.objects.filter(promise_id=promise.id).first()
            promise_data.append({
                "promise": promise.promise,
                "status": implementation.status if implementation else "PENDING",
            })

        return {
            "average_rating": average_rating,
            "promises": promise_data,
        }