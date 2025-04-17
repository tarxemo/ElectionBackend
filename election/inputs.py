import graphene
from graphene import InputObjectType, DateTime, Decimal, ID

# Input Object for University
class UniversityInput(InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()

# Input Object for College
class CollegeInput(InputObjectType):
    name = graphene.String(required=True)
    university_id = graphene.ID(required=True)
    description = graphene.String()

# Input Object for Hostel
class HostelInput(InputObjectType):
    name = graphene.String(required=True)
    college_id = graphene.ID(required=True)
    description = graphene.String()

# Input Object for Student Registration
class StudentRegistrationInput(InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    hostel_id = graphene.ID(required=True)
    college_id = graphene.ID(required=True)
    university_id = graphene.ID(required=True)
    is_candidate = graphene.Boolean(default=False)

# Input Object for Position
class PositionInput(InputObjectType):
    name = graphene.String(required=True)
    level = graphene.String(required=True)
    description = graphene.String()

# Input Object for Candidate
class CandidateInput(InputObjectType):
    student_id = graphene.ID(required=True)
    position_id = graphene.ID(required=True)
    manifesto = graphene.String()

# Input Object for Election
class ElectionInput(InputObjectType):
    name = graphene.String(required=True)
    level = graphene.String(required=True)
    start_date = DateTime(required=True)
    end_date = DateTime(required=True)
    position_ids = graphene.List(graphene.ID, required=True)
    description = graphene.String()

# Input Object for Vote
class VoteInput(InputObjectType):
    student_id = graphene.ID(required=True)
    candidate_id = graphene.ID(required=True)
    election_id = graphene.ID(required=True)

# Input Object for LeaderPromise
class LeaderPromiseInput(InputObjectType):
    candidate_id = graphene.ID(required=True)
    promise = graphene.String(required=True)

# Input Object for PromiseImplementation
class PromiseImplementationInput(InputObjectType):
    promise_id = graphene.ID(required=True)
    status = graphene.String(required=True)
    update = graphene.String()

# Input Object for LeaderRating
class LeaderRatingInput(InputObjectType):
    leader_id = graphene.ID(required=True)
    student_id = graphene.ID(required=True)
    rating = graphene.Int(required=True)
    comment = graphene.String()