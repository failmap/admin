"""Test assumptions about task composition."""


from celery import group

from failmap.celery import debug_task

TIMEOUT = 10


def test_chords(celery_app, celery_worker, queues):
    """A set of tasks should complete irregardless of the amount of chords, tasks or groups.

    In onboarding a group of discovery tasks is run before taskshe 'onboard finish' task (which
    implicitly creates a chord). However having multiple of these (multiple url endpoints to
    discover) causes the entire set to hang. This test should prove that the underlying principle
    (multiple group/chord combinations in a group) works.
    """

    task = group([
        group([
            debug_task.si("store_url_ips_task"),
            debug_task.si("kill_url_task"),
            debug_task.si("revive_url_task"),
        ]) | debug_task.si("finish_onboarding"),
        group([
            debug_task.si("store_url_ips_task"),
            debug_task.si("kill_url_task"),
            debug_task.si("revive_url_task"),
        ]) | debug_task.si("finish_onboarding"),
    ])
    print("Task:", task)
    async_result = task.apply_async(queue=queues[0])
    result = async_result.get(timeout=TIMEOUT)
    print("Result:", result)
    assert result
