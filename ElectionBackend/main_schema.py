# from election.queries.macqueries import CollegeQuery
from election.queries.positions import PositionQuery
# from election.queries.macqueries import CollegeQuery, PositionCandidateQuery  
from election.mutations.mutations import Mutation
import graphene
# from election.statistics import StatisticsQuery
# from election.views import Mutation
# from election.schema import Query

class RootQuery(PositionQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)

