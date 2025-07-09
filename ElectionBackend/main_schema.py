from election.queries.simulate_votes import VoteMutation, VoteQuery
from election.mutations.mutations import Mutation
from election.queries.positions import PositionQuery
# from election.queries.subscriptions import ActiveElectionSubscription  # Import the subscription class

import graphene

class RootQuery(PositionQuery, VoteQuery, graphene.ObjectType):
    pass

class RootMutation(Mutation, VoteMutation, graphene.ObjectType):
    pass

# class RootSubscription(ActiveElectionSubscription, graphene.ObjectType):  # Include subscription class
#     pass

schema = graphene.Schema(query=RootQuery, mutation=RootMutation)
