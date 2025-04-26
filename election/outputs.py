import graphene
from graphene import ObjectType, DateTime, Decimal, UUID
from .models import University, College, Hostel, Student, Position, Candidate, Election, Vote, LeaderPromise, PromiseImplementation, LeaderRating

class ElectionStats(graphene.ObjectType):
    active_elections = graphene.Int()
    total_votes = graphene.Int()
    registered_voters = graphene.Int()
    total_candidates = graphene.Int()
    participation_rate = graphene.Float()
    
# Output Object for User
class UserOutput(ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()

# Output Object for University
class UniversityOutput(ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()

# Output Object for College
class CollegeOutput(ObjectType):
    id = graphene.ID()
    name = graphene.String()
    university = graphene.Field(UniversityOutput)
    description = graphene.String()

# Output Object for Hostel
class HostelOutput(ObjectType):
    id = graphene.ID()
    name = graphene.String()
    college = graphene.Field(CollegeOutput)
    description = graphene.String()

# Output Object for Student
class StudentOutput(ObjectType):
    id = graphene.ID()
    user = graphene.Field(UserOutput)  # Assuming you have a UserOutput type for the User model
    hostel = graphene.Field(HostelOutput)
    college = graphene.Field(CollegeOutput)
    university = graphene.Field(UniversityOutput)
    is_candidate = graphene.Boolean()

# Output Object for Position
class PositionOutput(ObjectType):
    id = graphene.ID()
    name = graphene.String()
    level = graphene.String()
    description = graphene.String()

# Output Object for Candidate
class CandidateOutput(ObjectType):
    id = graphene.ID()
    student = graphene.Field(StudentOutput)
    position = graphene.Field(PositionOutput)
    manifesto = graphene.String()

# Output Object for Election
class ElectionOutput(ObjectType):
    id = graphene.ID()
    name = graphene.String()
    level = graphene.String()
    start_date = DateTime()
    end_date = DateTime()
    positions = graphene.List(PositionOutput)
    description = graphene.String()

# Output Object for Vote
class VoteOutput(ObjectType):
    id = graphene.ID()
    student = graphene.Field(StudentOutput)
    candidate = graphene.Field(CandidateOutput)
    election = graphene.Field(ElectionOutput)
    timestamp = DateTime()

# Output Object for LeaderPromise
class LeaderPromiseOutput(ObjectType):
    id = graphene.ID()
    candidate = graphene.Field(CandidateOutput)
    promise = graphene.String()
    timestamp = DateTime()

# Output Object for PromiseImplementation
class PromiseImplementationOutput(ObjectType):
    id = graphene.ID()
    promise = graphene.Field(LeaderPromiseOutput)
    status = graphene.String()
    update = graphene.String()
    timestamp = DateTime()

# Output Object for LeaderRating
class LeaderRatingOutput(ObjectType):
    id = graphene.ID()
    leader = graphene.Field(CandidateOutput)
    student = graphene.Field(StudentOutput)
    rating = graphene.Int()
    comment = graphene.String()
    timestamp = DateTime()