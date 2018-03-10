#!/usr/bin/env python3

import logging

import dramatiq
import dramatiq.brokers.redis
from failmap.dramatiq import ping

# logging.basicConfig(level=logging.DEBUG)
# broker = dramatiq.brokers.redis.RedisBroker()
# dramatiq.set_broker(broker)

#
# class actor:
#     """Shim dramatiq actor to allow-just-in time instantiation of the actor.
#
#     Whenever an dramatiq actor is declared (via decorator) it will be instantiated
#     at that point. Which results in the global broker singleton being created with
#     the configuration set at that time. Since actors are preferrably created using
#     decorators this means that this will likely be during import time. This is not
#     optimal as broker configuration might have been dynamically generated after
#     import time or dramatiq is not required but just because a actor is imported
#     somewhere else in the code the entire initialisation will be ran (eg: even for
#     a `failmap --help`).
#     """
#
#     def __init__(self, fn, *args, **kwargs):
#         """Save everything required to perform a delayed decorate."""
#         self._actor = None
#         self._fn = fn
#         self._args = args
#         self._kwargs = kwargs
#
#     def __getattr__(self, name):
#         """This first time a actor method is called upon (eg: task.send()), intialize the actor."""
#         if not self._actor:
#             actor = dramatiq.actor(fn=self._fn, **self._kwargs)
#             self._actor = actor
#         return getattr(self._actor, name)

# def actor(fn):
#     print(1)
#
#     def dec(*args):
#         print(2)
#     return dec
#


# @dramatiq.actor
# def test():
#     print('test')


# @actor
# def test():
#     print('test')
#
#
# print(test, type(test), dir(test))
# print(test.send)
#
# test.send()

ping.send()
