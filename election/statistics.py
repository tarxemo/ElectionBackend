import graphene
from graphene_django.types import DjangoObjectType
from django.db.models import Count, Avg, F
from .models import *

# GraphQL Types
class VoteType(DjangoObjectType):
    class Meta:
        model = Vote

class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate

class ElectionType(DjangoObjectType):
    class Meta:
        model = Election

class CollegeType(DjangoObjectType):
    class Meta:
        model = College

class HostelType(DjangoObjectType):
    class Meta:
        model = Hostel

class UniversityType(DjangoObjectType):
    class Meta:
        model = University

class LeaderRatingType(DjangoObjectType):
    class Meta:
        model = LeaderRating

class PromiseImplementationType(DjangoObjectType):
    class Meta:
        model = PromiseImplementation

class PositionType(DjangoObjectType):
    class Meta:
        model = Position

# Query Resolvers
class StatisticsQuery(graphene.ObjectType):
    # 1. Total Votes per Candidate in a Specific Election
    total_votes_per_candidate = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_total_votes_per_candidate(self, info, election_id):
        return Candidate.objects.filter(position__elections__id=election_id) \
            .annotate(total_votes=Count('votes')) \
            .values('student__user__username', 'total_votes')

    # 2. Vote Distribution Across Colleges in a University Election
    vote_distribution_across_colleges = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_distribution_across_colleges(self, info, election_id):
        return College.objects.filter(students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 3. Vote Trends Over Time for a Specific Election
    vote_trends_over_time = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_trends_over_time(self, info, election_id):
        return Vote.objects.filter(election__id=election_id) \
            .extra(select={'timestamp': "DATE(timestamp)"}) \
            .values('timestamp') \
            .annotate(total_votes=Count('id'))

    # 4. Comparison of Vote Counts Between Hostels in a College Election
    vote_comparison_between_hostels = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_comparison_between_hostels(self, info, election_id):
        return Hostel.objects.filter(college__students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 5. Leader Ratings Over Time
    leader_ratings_over_time = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_leader_ratings_over_time(self, info, candidate_id):
        return LeaderRating.objects.filter(leader__id=candidate_id) \
            .extra(select={'timestamp': "DATE(timestamp)"}) \
            .values('timestamp') \
            .annotate(average_rating=Avg('rating'))

    # 6. Comparison of Average Ratings Between Candidates in a College
    average_ratings_comparison = graphene.List(
        graphene.JSONString,
        college_id=graphene.ID(required=True)
    )

    def resolve_average_ratings_comparison(self, info, college_id):
        return Candidate.objects.filter(student__college__id=college_id) \
            .annotate(average_rating=Avg('ratings__rating')) \
            .values('student__user__username', 'average_rating')

    # 7. Promise Implementation Status for a Candidate
    promise_implementation_status = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_promise_implementation_status(self, info, candidate_id):
        return PromiseImplementation.objects.filter(promise__candidate__id=candidate_id) \
            .values('status') \
            .annotate(count=Count('id'))

    # 8. Voter Turnout by College in a University Election
    voter_turnout_by_college = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_voter_turnout_by_college(self, info, election_id):
        return College.objects.filter(students__votes__election__id=election_id) \
            .annotate(
                total_voters=Count('students', distinct=True),
                total_votes=Count('students__votes')
            ) \
            .values('name', 'total_voters', 'total_votes')

    # 9. Top 5 Candidates by Votes in a Specific Election
    top_candidates_by_votes = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_top_candidates_by_votes(self, info, election_id):
        return Candidate.objects.filter(position__elections__id=election_id) \
            .annotate(total_votes=Count('votes')) \
            .order_by('-total_votes')[:5] \
            .values('student__user__username', 'total_votes')

    # 10. Vote Distribution by Position in an Election
    vote_distribution_by_position = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_distribution_by_position(self, info, election_id):
        return Position.objects.filter(elections__id=election_id) \
            .annotate(total_votes=Count('candidates__votes')) \
            .values('name', 'total_votes')

    # 11. Comparison of Vote Counts Between Universities
    vote_comparison_between_universities = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_vote_comparison_between_universities(self, info, election_id):
        return University.objects.filter(students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 12. Trend of Votes for a Candidate Over Multiple Elections
    votes_trend_for_candidate = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_votes_trend_for_candidate(self, info, candidate_id):
        return Vote.objects.filter(candidate__id=candidate_id) \
            .values('election__name') \
            .annotate(total_votes=Count('id'))

    # 13. Comparison of Promise Implementation Status Between Candidates
    promise_implementation_comparison = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_promise_implementation_comparison(self, info, election_id):
        return Candidate.objects.filter(position__elections__id=election_id) \
            .annotate(
                completed_promises=Count('promises__implementations', filter=Q(promises__implementations__status='COMPLETED')),
                pending_promises=Count('promises__implementations', filter=Q(promises__implementations__status='PENDING'))
            ) \
            .values('student__user__username', 'completed_promises', 'pending_promises')

    # 14. Voter Turnout by Hostel in a College Election
    voter_turnout_by_hostel = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_voter_turnout_by_hostel(self, info, election_id):
        return Hostel.objects.filter(college__students__votes__election__id=election_id) \
            .annotate(
                total_voters=Count('students', distinct=True),
                total_votes=Count('students__votes')
            ) \
            .values('name', 'total_voters', 'total_votes')

    # 15. Comparison of Ratings Between Hostel Leaders
    ratings_comparison_between_hostel_leaders = graphene.List(
        graphene.JSONString,
        hostel_id=graphene.ID(required=True)
    )

    def resolve_ratings_comparison_between_hostel_leaders(self, info, hostel_id):
        return Candidate.objects.filter(student__hostel__id=hostel_id) \
            .annotate(average_rating=Avg('ratings__rating')) \
            .values('student__user__username', 'average_rating')

    # 16. Trend of Ratings for a Leader Over Time
    ratings_trend_for_leader = graphene.List(
        graphene.JSONString,
        candidate_id=graphene.ID(required=True)
    )

    def resolve_ratings_trend_for_leader(self, info, candidate_id):
        return LeaderRating.objects.filter(leader__id=candidate_id) \
            .extra(select={'timestamp': "DATE(timestamp)"}) \
            .values('timestamp') \
            .annotate(average_rating=Avg('rating'))

    # 17. Comparison of Votes Between Candidates for a Specific Position
    votes_comparison_for_position = graphene.List(
        graphene.JSONString,
        position_id=graphene.ID(required=True)
    )

    def resolve_votes_comparison_for_position(self, info, position_id):
        return Candidate.objects.filter(position__id=position_id) \
            .annotate(total_votes=Count('votes')) \
            .values('student__user__username', 'total_votes')

    # 18. Voter Turnout by University in All Elections
    voter_turnout_by_university = graphene.List(
        graphene.JSONString
    )

    def resolve_voter_turnout_by_university(self, info):
        return University.objects.annotate(
            total_voters=Count('students', distinct=True),
            total_votes=Count('students__votes')
        ) \
            .values('name', 'total_voters', 'total_votes')

    # 19. Comparison of Votes Between Colleges in a University Election
    votes_comparison_between_colleges = graphene.List(
        graphene.JSONString,
        election_id=graphene.ID(required=True)
    )

    def resolve_votes_comparison_between_colleges(self, info, election_id):
        return College.objects.filter(students__votes__election__id=election_id) \
            .annotate(total_votes=Count('students__votes')) \
            .values('name', 'total_votes')

    # 20. Trend of Votes for a Position Over Multiple Elections
    votes_trend_for_position = graphene.List(
        graphene.JSONString,
        position_id=graphene.ID(required=True)
    )

    def resolve_votes_trend_for_position(self, info, position_id):
        return Vote.objects.filter(candidate__position__id=position_id) \
            .values('election__name') \
            .annotate(total_votes=Count('id'))
            
    # 1. College List
    college_list = graphene.List(CollegeType)

    def resolve_college_list(self, info):
        return College.objects.all()

    # 2. College Details
    college_details = graphene.Field(CollegeType, college_id=graphene.ID(required=True))

    def resolve_college_details(self, info, college_id):
        return College.objects.get(id=college_id)

    # 3. Candidate List
    candidate_list = graphene.List(CandidateType)

    def resolve_candidate_list(self, info):
        return Candidate.objects.all()

    # 4. Candidate Details
    candidate_details = graphene.Field(CandidateType, candidate_id=graphene.ID(required=True))

    def resolve_candidate_details(self, info, candidate_id):
        return Candidate.objects.get(id=candidate_id)

    # 5. University Details
    university_details = graphene.Field(UniversityType, university_id=graphene.ID(required=True))

    def resolve_university_details(self, info, university_id):
        return University.objects.get(id=university_id)

    # 6. Hostel List
    hostel_list = graphene.List(HostelType)

    def resolve_hostel_list(self, info):
        return Hostel.objects.all()

    # 7. Hostel Details
    hostel_details = graphene.Field(HostelType, hostel_id=graphene.ID(required=True))

    def resolve_hostel_details(self, info, hostel_id):
        return Hostel.objects.get(id=hostel_id)

    # 8. Hostels for a Given College
    hostels_for_college = graphene.List(HostelType, college_id=graphene.ID(required=True))

    def resolve_hostels_for_college(self, info, college_id):
        return Hostel.objects.filter(college_id=college_id)

    # 9. Position List
    position_list = graphene.List(PositionType)

    def resolve_position_list(self, info):
        return Position.objects.all()

    # 10. Position Details
    position_details = graphene.Field(PositionType, position_id=graphene.ID(required=True))

    def resolve_position_details(self, info, position_id):
        return Position.objects.get(id=position_id)

    # 11. Election List
    election_list = graphene.List(ElectionType)

    def resolve_election_list(self, info):
        return Election.objects.all()

    # 12. Election Details
    election_details = graphene.Field(ElectionType, election_id=graphene.ID(required=True))

    def resolve_election_details(self, info, election_id):
        return Election.objects.get(id=election_id)