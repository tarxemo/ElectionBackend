# schema.py
import graphene
from graphene_django import DjangoObjectType
from election.types import VoteType
from election.outputs import *
from election.models import *
from django.utils import timezone
import datetime
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
# class ElectionType(DjangoObjectType):
#     class Meta:
#         model = Election
#         fields = "__all__"
        
#     is_active = graphene.Boolean()
    
#     def resolve_is_active(self, info):
#         now = timezone.now()
#         return self.start_datetime <= now <= self.end_datetime and self.status == 'ACTIVE'

# class PositionType(DjangoObjectType):
#     class Meta:
#         model = Position
#         fields = "__all__"

# class ElectionPositionType(DjangoObjectType):
#     class Meta:
#         model = ElectionPosition
#         fields = "__all__"

# class CandidateType(DjangoObjectType):
#     class Meta:
#         model = Candidate
#         fields = "__all__"
        
#     total_votes = graphene.Int()
    
#     def resolve_total_votes(self, info):
#         return self.votes.count()

# class VoteType(DjangoObjectType):
#     class Meta:
#         model = Vote
#         fields = "__all__"

class VoteQuery(graphene.ObjectType):
    active_elections = graphene.List(ElectionOutput)
    election_positions = graphene.List(ElectionPositionOutput, election_id=graphene.ID(required=True))
    position_candidates = graphene.List(CandidateOutput, election_position_id=graphene.ID(required=True))
    
    def resolve_active_elections(self, info):
        now = timezone.now()
        return Election.objects.filter(
            # start_datetime__lte=now,
            # end_datetime__gte=now,
            status='ACTIVE'
        )
    
    def resolve_election_positions(self, info, election_id):
        return ElectionPosition.objects.filter(election_id=election_id)
    
    def resolve_position_candidates(self, info, election_position_id):
        return Candidate.objects.filter(
            election_position_id=election_position_id,
            is_approved=True
        )
        
    eligible_voters = graphene.List(
        StudentOutput,
        election_id=graphene.ID(required=True),
        search=graphene.String()
    )
    
    def resolve_eligible_voters(self, info, election_id, search=None):
        try:
            election = Election.objects.get(pk=election_id)
            print(election.institution)
            # qs = Student.objects.filter(
            #     institution__in=get_eligible_institutions(election.institution),
            #     academic_year=election.academic_year,
            #     is_active=True
            # ).select_related('user', 'institution', 'academic_year')
            
            qs = Student.objects.all()[200:400]
            # if search:
            #     qs = qs.filter(
            #         Q(user__first_name__icontains=search) |
            #         Q(user__last_name__icontains=search) |
            #         Q(user__username__icontains=search)
            #     )
            
            return qs
        except Election.DoesNotExist:
            return []

def get_eligible_institutions(institution):
    """
    Recursively find all institutions under the given parent that have no children.
    """
    if institution is None:
        return []

    if not institution.children.exists():
        return [institution]

    bottom_most = []
    for child in institution.children.all():
        bottom_most.extend(get_eligible_institutions(child))
        print(bottom_most.name)

    return bottom_most




class CastVoteInput(graphene.InputObjectType):
    election_id = graphene.ID(required=True)
    candidate_id = graphene.ID(required=True)
    voter_id = graphene.ID(required=True)

class CastVotesInput(graphene.InputObjectType):
    votes = graphene.List(CastVoteInput, required=True)

class CastVotePayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    vote = graphene.Field(VoteType)

class CastVotesPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    votes = graphene.List(VoteType)

class VoteMutation(graphene.ObjectType):
    cast_vote = graphene.Field(
        CastVotePayload,
        input=CastVoteInput(required=True)
    )
    
    cast_votes = graphene.Field(
        CastVotesPayload,
        input=CastVotesInput(required=True)
    )
    

    def resolve_cast_vote(self, info, input):
        try:
            election = Election.objects.get(pk=input.election_id)
            candidate = Candidate.objects.get(pk=input.candidate_id)
            voter = Student.objects.get(pk=input.voter_id)
            
            # Check if election is active
            now = timezone.now()
            if not (election.start_datetime <= now <= election.end_datetime and election.status == 'ACTIVE'):
                return CastVotePayload(
                    success=False,
                    message="Election is not currently active"
                )
            
            # Check if voter has already voted for this position
            existing_vote = Vote.objects.filter(
                election=election,
                voter=voter,
                candidate__election_position=candidate.election_position
            ).exists()
            
            if existing_vote:
                return CastVotePayload(
                    success=False,
                    message="You have already voted for this position"
                )
            
            # Create the vote
            vote = Vote.objects.create(
                election=election,
                candidate=candidate,
                voter=voter,
                weight=1
            )
            
            return CastVotePayload(
                success=True,
                message="Vote cast successfully",
                vote=vote
            )
            
        except Exception as e:
            return CastVotePayload(
                success=False,
                message=str(e)
            )

    

    def resolve_cast_votes(self, info, input):
        from django.utils import timezone
        from graphql import GraphQLError
        try:
            votes_data = []
            created_votes = []
            now = timezone.now()

            for vote_input in input.votes:
                # Fetch required objects
                try:
                    election = Election.objects.get(pk=vote_input.election_id)
                    candidate = Candidate.objects.get(pk=vote_input.candidate_id)
                    voter = Student.objects.get(pk=vote_input.voter_id)
                except Election.DoesNotExist:
                    raise GraphQLError(f"Election with ID {vote_input.election_id} does not exist")
                except Candidate.DoesNotExist:
                    raise GraphQLError(f"Candidate with ID {vote_input.candidate_id} does not exist")
                except Student.DoesNotExist:
                    raise GraphQLError(f"Student with ID {vote_input.voter_id} does not exist")

                # Ensure election datetimes are timezone-aware
                start_dt = election.start_datetime
                end_dt = election.end_datetime

                if timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt)
                if timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt)

                # Election must be active and within time
                if not (start_dt <= now <= end_dt and election.status == 'ACTIVE'):
                    raise GraphQLError(f"Election '{election.name}' is not currently active")

                # Check if the voter has already voted for this position in this election
                has_voted = Vote.objects.filter(
                    election=election,
                    voter=voter,
                    candidate__election_position=candidate.election_position
                ).exists()

                if has_voted:
                    raise GraphQLError(
                        f"You have already voted for position '{candidate.election_position.position.name}' in election '{election.name}'"
                    )

                # Append validated vote info
                votes_data.append({
                    'election': election,
                    'candidate': candidate,
                    'voter': voter
                })

            # All votes are valid, proceed to create them
            for vote_data in votes_data:
                vote = Vote.objects.create(
                    election=vote_data['election'],
                    candidate=vote_data['candidate'],
                    voter=vote_data['voter'],
                    weight=1  # default weight
                )
                created_votes.append(vote)

            return CastVotesPayload(
                success=True,
                message="All votes cast successfully",
                votes=created_votes
            )

        except GraphQLError as e:
            return CastVotesPayload(success=False, message=str(e))
        except Exception as e:
            return CastVotesPayload(success=False, message="Unexpected error: " + str(e))

