"""Test assumptions about task composition."""


from celery import chord, group

from failmap.celery import debug_task

TIMEOUT = 10


def test_chords(celery_app, celery_worker, queues):
    """A set of tasks should complete irregardless of the amount of chords, tasks or groups.

    In onboarding a group of discovery tasks is run before taskshe 'onboard finish' task (which
    implicitly creates a chord). However having multiple of these (multiple url endpoints to
    discover) causes the entire set to hang. This test should prove that the underlying principle
    (multiple group/chord combinations in a group) works.
    """

    task = chord(group([
        debug_task.si('get_ips1'),  # | debug_task.si("can_connect_ips"),  # | debug_task.si("connect_result"),
        # debug_task.si('get_ips2'),  # | debug_task.si("can_connect_ips"),  # | debug_task.si("connect_result"),
        # debug_task.si('get_ips'),  # | debug_task.si("can_connect_ips"),  # | debug_task.si("connect_result"),

        debug_task.si('get_ips3') | group([
            debug_task.si("store_url_ips_task"),
            # debug_task.si("kill_url_task"),
            # debug_task.si("revive_url_task"),
        ]) | debug_task.si('collect'),

        # group([debug_task.si('get_ips') | group([
        #     debug_task.si("store_url_ips_task"),
        #     debug_task.si("kill_url_task"),
        #     debug_task.si("revive_url_task"),
        # ])]),
        # debug_task.si('get_ips') | debug_task.si("can_connect_ips"), debug_task.si("connect_result"),
        # debug_task.si('get_ips') | debug_task.si("can_connect_ips"), debug_task.si("connect_result"),

    ]), body=debug_task.si("finish_onboarding", returns=True))

    task2 = group([
        debug_task.si('get_ips3') |
        group([
            debug_task.si("store_url_ips_task"),
            debug_task.si("kill_url_task")
        ]) | debug_task.si('collect')
    ]) | debug_task.si("finish_onboarding", returns=True)

    # works
    # task3 = chord(header=debug_task.si('get_ips3') | group([
    #     debug_task.si("store_url_ips_task"),
    #     debug_task.si("kill_url_task")
    # ]) | debug_task.si('collect'), body=debug_task.si("finish_onboarding", returns=True))

    print("Task :", task)
    print("Task2:", task2)
    # print("Task3:", task3)
    async_result = task.apply_async(queue=queues[0])
    result = async_result.get(timeout=TIMEOUT)
    print("Result :", result)
    assert result

    async_result2 = task2.apply_async(queue=queues[0])
    result2 = async_result2.get(timeout=TIMEOUT)
    print("Result2:", result2)
    assert result2
