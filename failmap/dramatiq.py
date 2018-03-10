import logging
import os

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.results.backends import RedisBackend, StubBackend

log = logging.getLogger(__name__)


def setbroker(watcher=False):
    broker_url = os.environ.get('BROKER', 'redis://localhost:6379/0')
    log.debug('Initializing dramatiq with broker: %s', broker_url)

    if broker_url.startswith('redis'):
        broker = RedisBroker(url=broker_url)
        broker.add_middleware(dramatiq.results.Results(backend=RedisBackend(client=broker.client)))
    else:
        broker = StubBroker()
        broker.add_middleware(dramatiq.results.Results(backend=StubBackend()))

    broker.add_middleware(dramatiq.middleware.AgeLimit())
    broker.add_middleware(dramatiq.middleware.Callbacks())
    broker.add_middleware(dramatiq.middleware.Retries())
    broker.add_middleware(dramatiq.middleware.Pipelines())

    dramatiq.set_broker(broker)
    dramatiq.set_encoder(dramatiq.PickleEncoder)


setbroker()


class actor:
    """Shim dramatiq actor to allow-just-in time instantiation of the actor.

    Whenever an dramatiq actor is declared (via decorator) it will be instantiated
    at that point. Which results in the global broker singleton being created with
    the configuration set at that time. Since actors are preferrably created using
    decorators this means that this will likely be during import time. This is not
    optimal as broker configuration might have been dynamically generated after
    import time or dramatiq is not required but just because a actor is imported
    somewhere else in the code the entire initialisation will be ran (eg: even for
    a `failmap --help`).
    """

    def __init__(self, fn=None, **kwargs):
        """Save everything required to perform a delayed decorate."""
        self._actor = None
        if fn:
            self._fn = fn
        else:
            self._kwargs = kwargs
        if dramatiq.broker.global_broker and fn:
            self._actor = dramatiq.actor(**kwargs)(fn)

    def __call__(self, fn):
        self._fn = fn
        return self

    def __getattr__(self, name):
        """This first time a actor method is called upon (eg: task.send()), intialize the actor."""
        if not self._actor:
            log.debug('Initializing actor %s for %s', str(self._fn), name)
            self._actor = dramatiq.actor(fn=self._fn, **self._kwargs)
        print(self._actor)
        return getattr(self._actor, name)


@actor(store_results=True)
def ping():
    return 'pong'
