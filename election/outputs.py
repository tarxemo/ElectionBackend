# output.py
import graphene
from graphene_django.types import DjangoObjectType
from .models import (
    AcademicYear,
    InstitutionLevel,
    Institution,
    Position,
    Student,
    Election,
    ElectionPosition,
    Candidate,
    Vote,
    ElectionResult,
    Leader,
    Promise,
    PromiseUpdate,
    Rating,
    ElectionStatistics
)

class UserOutput(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    is_active = graphene.Boolean()
    date_joined = graphene.DateTime()

class AcademicYearOutput(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    start_date = graphene.Date()
    end_date = graphene.Date()
    is_current = graphene.Boolean()

class InstitutionLevelOutput(graphene.ObjectType):
    id = graphene.ID()
    level = graphene.String()
    display_level = graphene.String()
    
    def resolve_display_level(self, info):
        return self.get_level_display()

class InstitutionOutput(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    level = graphene.Field(InstitutionLevelOutput)
    parent = graphene.Field(lambda: InstitutionOutput)
    description = graphene.String()
    created_at = graphene.DateTime()

class PositionOutput(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    level = graphene.Field(InstitutionLevelOutput)
    institution = graphene.Field(InstitutionOutput)
    voting_power = graphene.Int()

class StudentOutput(graphene.ObjectType):
    id = graphene.ID()
    user = graphene.Field(UserOutput)
    institution = graphene.Field(InstitutionOutput)
    academic_year = graphene.Field(AcademicYearOutput)
    is_active = graphene.Boolean()
    is_candidate = graphene.Boolean()
    
    # Additional fields for specific institution types
    hostel = graphene.Field(lambda: InstitutionOutput)
    college = graphene.Field(lambda: InstitutionOutput)
    university = graphene.Field(lambda: InstitutionOutput)
    
    def resolve_hostel(self, info):
        if self.institution.level.level == 'HOSTEL':
            return self.institution
        return None
    
    def resolve_college(self, info):
        if self.institution.level.level == 'COLLEGE':
            return self.institution
        return None
    
    def resolve_university(self, info):
        if self.institution.level.level == 'UNIVERSITY':
            return self.institution
        return None

class ElectionOutput(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    status = graphene.String()
    display_status = graphene.String()
    start_datetime = graphene.DateTime()
    end_datetime = graphene.DateTime()
    academic_year = graphene.Field(AcademicYearOutput)
    level = graphene.Field(InstitutionLevelOutput)
    institution = graphene.Field(InstitutionOutput)
    is_active = graphene.Boolean()
    
    def resolve_display_status(self, info):
        return self.get_status_display()
    
    def resolve_is_active(self, info):
        from django.utils import timezone
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime and self.status == 'ACTIVE'

class ElectionPositionOutput(graphene.ObjectType):
    id = graphene.ID()
    election = graphene.Field(ElectionOutput)
    position = graphene.Field(PositionOutput)
    max_candidates = graphene.Int()

class CandidateOutput(graphene.ObjectType):
    id = graphene.ID()
    student = graphene.Field(StudentOutput)
    election_position = graphene.Field(ElectionPositionOutput)
    manifesto = graphene.String()
    is_approved = graphene.Boolean()
    approved_at = graphene.DateTime()
    created_at = graphene.DateTime()
    total_votes = graphene.Int()
    
    def resolve_total_votes(self, info):
        return self.votes.count()

class VoteOutput(graphene.ObjectType):
    id = graphene.ID()
    election = graphene.Field(ElectionOutput)
    candidate = graphene.Field(CandidateOutput)
    voter = graphene.Field(StudentOutput)
    timestamp = graphene.DateTime()
    weight = graphene.Int()

class ElectionResultOutput(graphene.ObjectType):
    id = graphene.ID()
    election = graphene.Field(ElectionOutput)
    candidate = graphene.Field(CandidateOutput)
    total_votes = graphene.Int()
    percentage = graphene.Float()
    position_rank = graphene.Int()
    is_winner = graphene.Boolean()
    calculated_at = graphene.DateTime()

class LeaderOutput(graphene.ObjectType):
    id = graphene.ID()
    candidate = graphene.Field(CandidateOutput)
    position = graphene.Field(PositionOutput)
    institution = graphene.Field(InstitutionOutput)
    start_date = graphene.Date()
    end_date = graphene.Date()
    is_active = graphene.Boolean()

class PromiseOutput(graphene.ObjectType):
    id = graphene.ID()
    candidate = graphene.Field(CandidateOutput)
    title = graphene.String()
    description = graphene.String()
    created_at = graphene.DateTime()

class PromiseUpdateOutput(graphene.ObjectType):
    id = graphene.ID()
    promise = graphene.Field(PromiseOutput)
    status = graphene.String()
    display_status = graphene.String()
    update = graphene.String()
    timestamp = graphene.DateTime()
    
    def resolve_display_status(self, info):
        return self.get_status_display()

class RatingOutput(graphene.ObjectType):
    id = graphene.ID()
    leader = graphene.Field(LeaderOutput)
    student = graphene.Field(StudentOutput)
    score = graphene.Int()
    comment = graphene.String()
    timestamp = graphene.DateTime()

class ElectionStatisticsOutput(graphene.ObjectType):
    id = graphene.ID()
    election = graphene.Field(ElectionOutput)
    total_voters = graphene.Int()
    total_votes_cast = graphene.Int()
    voter_turnout = graphene.Float()
    leading_candidate = graphene.Field(CandidateOutput)
    calculated_at = graphene.DateTime()