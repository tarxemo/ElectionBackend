# from election.queries.institutionSchema import InstitutionQuery
# from  election.queries.colleges import CollegesQuery
from election.queries.simulate_votes import VoteMutation, VoteQuery
from election.mutations.mutations import Mutation
# from election.queries.candidate import CandidateQuery
from election.queries.positions import PositionQuery
# from election.queries.institutionSchema import InstitutionQuery

import graphene
# from election.statistics import StatisticsQuery
# from election.views import Mutation
# from election.schema import Query
class RootQuery(PositionQuery, VoteQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, VoteMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)

