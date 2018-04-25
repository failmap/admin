# rm -r env; virtualenv env --python=python3
# env/bin/pip install https://github.com/celery/celery/archive/c26e30bad8e141e80f2f62900474121ac52476ac.zip redis
# clear; env/bin/celery worker -A nested_chord_group_test:app -l info &
# sleep 2; env/bin/python -m nested_chord_group_test; pkill -f
# nested_chord_group_test:app


from celery import Celery, group

app = Celery(broker='redis://localhost/', backend='redis://localhost/')


@app.task(name="debug_task", bind=True)
def debug_task(self, *args, **kwargs):
    print("{} {}".format(args, kwargs))
    print(self.request)
    return kwargs.get('r')


if __name__ == "__main__":
    # this example passes
    task = group([
        debug_task.si(1) |
        group([
            debug_task.si(2),
            # debug_task.si(3)
        ]) | debug_task.si(4)
    ]) | debug_task.si(5, r=True)

    print(task)
    assert task.apply_async().get(timeout=10) is True
    print("PASS")

    # this example passes
    task = group([
        # debug_task.si(1) |
        group([
            debug_task.si(2),
            debug_task.si(3)
        ]) | debug_task.si(4)
    ]) | debug_task.si(5, r=True)

    print(task)
    assert task.apply_async().get(timeout=10) is True
    print("PASS")

    # this example passes
    task = group([
        debug_task.si(1) |
        group([
            debug_task.si(2),
            debug_task.si(3)
        ]) | debug_task.si(4)
    ])  # | debug_task.si(5, r=True)

    print(task)
    assert isinstance(task.apply_async().get(timeout=10), list)
    print("PASS")

    # this example fails
    task = group([
        debug_task.si(1) |
        group([
            debug_task.si(2),
            debug_task.si(3)
        ]) | debug_task.si(4)
    ]) | debug_task.si(5, r=True)

    print(task)
    assert task.apply_async().get(timeout=10) is True
    print("PASS")
