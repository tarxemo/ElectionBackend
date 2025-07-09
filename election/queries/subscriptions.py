# subscriptions.py
import graphene
from graphene_subscriptions.events import CREATED, UPDATED
from election.models import Election, ElectionStatistics
from election.outputs import ElectionOutput

class ActiveElectionSubscription(graphene.ObjectType):
    active_election_updated = graphene.Field(ElectionOutput)

    class Meta:
        description = "Subscription for updates on active elections"

    def resolve_active_election_updated(root, info):
        return root.filter(
            lambda event:
                event.operation in [CREATED, UPDATED] and
                isinstance(event.instance, (Election, ElectionStatistics)) and
                event.instance.status == 'ACTIVE'
        ).map(lambda event: event.instance)