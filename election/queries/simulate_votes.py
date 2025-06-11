# schema.py
import graphene
from graphene_django import DjangoObjectType
from election.outputs import *
from election.models import *
from django.utils import timezone

from django.db.models import Count, Sum, Avg, Q
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

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote
        fields = "__all__"

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
            
            qs = Student.objects.all()[:200]
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
                weight=1  # Default weight
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
        try:
            votes_data = []
            created_votes = []
            
            # First validate all votes
            for vote_input in input.votes:
                election = Election.objects.get(pk=vote_input.election_id)
                candidate = Candidate.objects.get(pk=vote_input.candidate_id)
                voter = Student.objects.get(pk=vote_input.voter_id)
                
                # Check if election is active
                now = timezone.now()
                if not (election.start_datetime <= now <= election.end_datetime and election.status == 'ACTIVE'):
                    raise Exception(f"Election {election.name} is not currently active")
                
                # Check if voter has already voted for this position
                existing_vote = Vote.objects.filter(
                    election=election,
                    voter=voter,
                    candidate__election_position=candidate.election_position
                ).exists()
                
                if existing_vote:
                    raise Exception(f"You have already voted for position {candidate.election_position.position.name}")
                
                votes_data.append({
                    'election': election,
                    'candidate': candidate,
                    'voter': voter
                })
            
            # If all validations pass, create all votes
            for vote_data in votes_data:
                vote = Vote.objects.create(
                    election=vote_data['election'],
                    candidate=vote_data['candidate'],
                    voter=vote_data['voter'],
                    weight=1  # Default weight
                )
                created_votes.append(vote)
            
            return CastVotesPayload(
                success=True,
                message="All votes cast successfully",
                votes=created_votes
            )
            
        except Exception as e:
            return CastVotesPayload(
                success=False,
                message=str(e)
            )
