import sched, time

s = sched.scheduler()
# https://docs.python.org/3.8/library/sched.html


def print_time(a="default"):
    print("From print_time", int(time.time()), a)


if __name__ == "__main__":
    s.enter(3, 1, print_time)
    s.enter(2, 2, print_time, argument=("important",))
    s.enter(2, 3, print_time, kwargs={"a": "less important"})
    print("Starting the show at", int(time.time()))
    s.run()
    print("Show finished at", int(time.time()))
