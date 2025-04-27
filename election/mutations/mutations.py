import graphene
from graphene_django import DjangoObjectType
from election.models import (
    AcademicYear, InstitutionLevel, Institution, Position,
    Student, Election, ElectionPosition, Candidate,
    Vote, ElectionResult, Leader, Promise, PromiseUpdate,
    Rating, ElectionStatistics
)
from django.utils import timezone

# GraphQL types
class AcademicYearType(DjangoObjectType):
    class Meta:
        model = AcademicYear
        fields = "__all__"

class ElectionType(DjangoObjectType):
    class Meta:
        model = Election
        fields = "__all__"

class CandidateType(DjangoObjectType):
    class Meta:
        model = Candidate
        fields = "__all__"

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote
        fields = "__all__"

# Mutations
class CreateElection(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        start_datetime = graphene.DateTime(required=True)
        end_datetime = graphene.DateTime(required=True)
        academic_year_id = graphene.ID(required=True)
        level_id = graphene.ID(required=True)
        institution_id = graphene.ID()

    election = graphene.Field(ElectionType)

    @classmethod
    def mutate(cls, root, info, name, start_datetime, end_datetime, academic_year_id, level_id, description=None, institution_id=None):
        academic_year = AcademicYear.objects.get(pk=academic_year_id)
        level = InstitutionLevel.objects.get(pk=level_id)
        institution = Institution.objects.get(pk=institution_id) if institution_id else None
        
        election = Election.objects.create(
            name=name,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            academic_year=academic_year,
            level=level,
            institution=institution
        )
        return CreateElection(election=election)

class RegisterCandidate(graphene.Mutation):
    class Arguments:
        student_id = graphene.ID(required=True)
        election_position_id = graphene.ID(required=True)
        manifesto = graphene.String()

    candidate = graphene.Field(CandidateType)

    @classmethod
    def mutate(cls, root, info, student_id, election_position_id, manifesto=None):
        student = Student.objects.get(pk=student_id)
        election_position = ElectionPosition.objects.get(pk=election_position_id)
        
        candidate = Candidate.objects.create(
            student=student,
            election_position=election_position,
            manifesto=manifesto,
            is_approved=False,
            created_at=timezone.now()
        )
        return RegisterCandidate(candidate=candidate)

class CastVote(graphene.Mutation):
    class Arguments:
        election_id = graphene.ID(required=True)
        candidate_id = graphene.ID(required=True)
        voter_id = graphene.ID(required=True)
        weight = graphene.Int(required=False)

    vote = graphene.Field(VoteType)

    @classmethod
    def mutate(cls, root, info, election_id, candidate_id, voter_id, weight=1):
        election = Election.objects.get(pk=election_id)
        candidate = Candidate.objects.get(pk=candidate_id)
        voter = Student.objects.get(pk=voter_id)

        # Check if the voter has already voted for this candidate
        if Vote.objects.filter(election=election, voter=voter, candidate=candidate).exists():
            raise Exception("You have already voted for this candidate.")

        vote = Vote.objects.create(
            election=election,
            candidate=candidate,
            voter=voter,
            weight=weight,
            timestamp=timezone.now()
        )
        return CastVote(vote=vote)

# Main Mutation class
class Mutation(graphene.ObjectType):
    create_election = CreateElection.Field()
    register_candidate = RegisterCandidate.Field()
    cast_vote = CastVote.Field()
