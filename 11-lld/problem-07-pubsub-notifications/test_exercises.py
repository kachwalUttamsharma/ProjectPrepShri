import dataclasses

import pytest

from exercises import *


class Recorder(Subscriber):
    def __init__(self, name="r", log=None):
        self.name = name
        self.log = log
        self.messages = []

    def handle(self, message):
        self.messages.append(message)
        if self.log is not None:
            self.log.append(self.name)


class Flaky(Subscriber):
    """Fails the first `fail_times` calls with RuntimeError."""

    def __init__(self, fail_times):
        self.fail_times = fail_times
        self.calls = 0
        self.messages = []

    def handle(self, message):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"boom {self.calls}")
        self.messages.append(message)


def make_broker(**kw):
    sleeps = []
    return PubSubBroker(sleeper=sleeps.append, **kw), sleeps


# ---- basics
def test_subscriber_is_abstract():
    with pytest.raises(TypeError):
        Subscriber()


def test_message_and_dead_letter_are_dataclasses():
    m = Message(1, "t", "p")
    assert dataclasses.is_dataclass(m)
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.payload = "x"


def test_publish_returns_message_with_sequential_ids():
    b, _ = make_broker()
    m1 = b.publish("a", "x")
    m2 = b.publish("b", "y")
    assert m1 == Message(1, "a", "x")
    assert m2 == Message(2, "b", "y")


def test_publish_without_subscribers_consumes_id_and_is_ok():
    b, _ = make_broker()
    b.publish("nobody", "x")
    assert b.publish("nobody", "y").message_id == 2


def test_delivery_to_subscriber():
    b, _ = make_broker()
    r = Recorder()
    b.subscribe("news", r)
    m = b.publish("news", "hello")
    assert r.messages == [m]


def test_delivery_in_subscription_order():
    b, _ = make_broker()
    log = []
    for n in ("first", "second", "third"):
        b.subscribe("t", Recorder(n, log))
    b.publish("t", "x")
    assert log == ["first", "second", "third"]


def test_topics_are_isolated():
    b, _ = make_broker()
    r1, r2 = Recorder(), Recorder()
    b.subscribe("a", r1)
    b.subscribe("b", r2)
    b.publish("a", "x")
    assert len(r1.messages) == 1 and r2.messages == []


def test_same_subscriber_on_two_topics():
    b, _ = make_broker()
    r = Recorder()
    b.subscribe("a", r)
    b.subscribe("b", r)
    b.publish("a", "1")
    b.publish("b", "2")
    assert [m.payload for m in r.messages] == ["1", "2"]


def test_subscribe_is_idempotent():
    b, _ = make_broker()
    r = Recorder()
    b.subscribe("t", r)
    b.subscribe("t", r)
    b.publish("t", "x")
    assert len(r.messages) == 1
    assert b.subscribers("t") == [r]


def test_unsubscribe():
    b, _ = make_broker()
    r = Recorder()
    b.subscribe("t", r)
    assert b.unsubscribe("t", r) is True
    assert b.unsubscribe("t", r) is False
    assert b.unsubscribe("unknown", r) is False
    b.publish("t", "x")
    assert r.messages == []


def test_subscribers_returns_copy():
    b, _ = make_broker()
    r = Recorder()
    b.subscribe("t", r)
    b.subscribers("t").clear()
    assert b.subscribers("t") == [r]
    assert b.subscribers("nope") == []


def test_unsubscribe_during_publish_uses_snapshot():
    b, _ = make_broker()
    late = Recorder("late")

    class Quitter(Subscriber):
        def handle(self, message):
            b.unsubscribe("t", late)

    b.subscribe("t", Quitter())
    b.subscribe("t", late)
    b.publish("t", "1")
    assert len(late.messages) == 1          # still got the in-flight message
    b.publish("t", "2")
    assert len(late.messages) == 1          # but not the next one


# ---- retry / backoff / dead letters
def test_retry_until_success_with_exponential_backoff():
    b, sleeps = make_broker(max_attempts=5, base_delay=1.0)
    f = Flaky(2)
    b.subscribe("t", f)
    m = b.publish("t", "x")
    assert f.calls == 3
    assert f.messages == [m]
    assert sleeps == [1.0, 2.0]
    assert b.dead_letters() == []


def test_custom_base_delay():
    b, sleeps = make_broker(max_attempts=4, base_delay=0.5)
    b.subscribe("t", Flaky(3))
    b.publish("t", "x")
    assert sleeps == [0.5, 1.0, 2.0]


def test_exhausted_retries_go_to_dead_letter_without_trailing_sleep():
    b, sleeps = make_broker(max_attempts=3, base_delay=1.0)
    f = Flaky(99)
    b.subscribe("t", f)
    m = b.publish("t", "x")
    assert f.calls == 3
    assert sleeps == [1.0, 2.0]             # no sleep after the final failure
    (dl,) = b.dead_letters()
    assert dl.message == m
    assert dl.subscriber is f
    assert dl.attempts == 3
    assert isinstance(dl.error, RuntimeError) and str(dl.error) == "boom 3"


def test_max_attempts_one_means_no_retry_no_sleep():
    b, sleeps = make_broker(max_attempts=1)
    f = Flaky(99)
    b.subscribe("t", f)
    b.publish("t", "x")
    assert f.calls == 1 and sleeps == []
    assert len(b.dead_letters()) == 1


def test_failing_subscriber_does_not_block_others_or_raise():
    b, _ = make_broker(max_attempts=2)
    before, after = Recorder("before"), Recorder("after")
    b.subscribe("t", before)
    b.subscribe("t", Flaky(99))
    b.subscribe("t", after)
    b.publish("t", "x")                      # must not raise
    assert len(before.messages) == 1 and len(after.messages) == 1
    assert len(b.dead_letters()) == 1


def test_each_message_retried_independently():
    b, sleeps = make_broker(max_attempts=2)
    f = Flaky(1)                             # only the very first call fails
    b.subscribe("t", f)
    b.publish("t", "1")
    b.publish("t", "2")
    assert [m.payload for m in f.messages] == ["1", "2"]
    assert sleeps == [1.0]


def test_dead_letters_returns_copy_in_creation_order():
    b, _ = make_broker(max_attempts=1)
    b.subscribe("t", Flaky(99))
    b.publish("t", "1")
    b.publish("t", "2")
    dls = b.dead_letters()
    assert [d.message.payload for d in dls] == ["1", "2"]
    dls.clear()
    assert len(b.dead_letters()) == 2


def test_base_exception_is_not_swallowed():
    class Interrupt(Subscriber):
        def handle(self, message):
            raise KeyboardInterrupt

    b, _ = make_broker()
    b.subscribe("t", Interrupt())
    with pytest.raises(KeyboardInterrupt):
        b.publish("t", "x")


def test_redrive():
    b, sleeps = make_broker(max_attempts=2)
    healed = Flaky(2)                        # fails both attempts, then works
    broken = Flaky(99)
    b.subscribe("t", healed)
    b.subscribe("t", broken)
    b.publish("t", "x")
    assert len(b.dead_letters()) == 2
    assert b.redrive_dead_letters() == 1
    remaining = b.dead_letters()
    assert len(remaining) == 1 and remaining[0].subscriber is broken
    assert len(healed.messages) == 1
    assert b.redrive_dead_letters() == 0
    assert len(b.dead_letters()) == 1


def test_validation():
    with pytest.raises(ValueError):
        PubSubBroker(max_attempts=0)
    with pytest.raises(ValueError):
        PubSubBroker(base_delay=-1)


# ---- notification service
def make_service(**channel_kw):
    sleeps = []
    broker = PubSubBroker(max_attempts=3, base_delay=1.0, sleeper=sleeps.append)
    ch = {"email": EmailChannel(**channel_kw.get("email", {})),
          "sms": SMSChannel(**channel_kw.get("sms", {})),
          "push": PushChannel(**channel_kw.get("push", {}))}
    return NotificationService(broker, ch), broker, ch, sleeps


def test_fake_channels():
    e = EmailChannel()
    assert e.name == "email" and SMSChannel().name == "sms" and PushChannel().name == "push"
    e.send("u1", "hi")
    assert e.sent == [("u1", "hi")] and e.calls == 1
    s = SMSChannel(fail_times=1)
    with pytest.raises(ChannelError):
        s.send("u1", "hi")
    s.send("u1", "hi")
    assert s.sent == [("u1", "hi")] and s.calls == 2


def test_channel_is_abstract():
    with pytest.raises(TypeError):
        Channel()


def test_default_preferences_email_only():
    svc, broker, ch, _ = make_service()
    assert svc.preferences("u1") == ["email"]
    svc.follow("u1", "deals")
    broker.publish("deals", "50% off")
    assert ch["email"].sent == [("u1", "50% off")]
    assert ch["sms"].sent == [] and ch["push"].sent == []


def test_custom_preferences_multi_channel():
    svc, broker, ch, _ = make_service()
    svc.set_preferences("u1", ["push", "sms"])
    assert svc.preferences("u1") == ["push", "sms"]
    svc.follow("u1", "deals")
    broker.publish("deals", "x")
    assert ch["push"].sent == [("u1", "x")] and ch["sms"].sent == [("u1", "x")]
    assert ch["email"].sent == []


def test_unknown_channel_rejected_and_state_unchanged():
    svc, *_ = make_service()
    with pytest.raises(ValueError):
        svc.set_preferences("u1", ["email", "pigeon"])
    assert svc.preferences("u1") == ["email"]
    with pytest.raises(ValueError):
        NotificationService(PubSubBroker(), {}, default_channels=("email",))


def test_empty_preferences_means_silence():
    svc, broker, ch, _ = make_service()
    svc.set_preferences("u1", [])
    svc.follow("u1", "t")
    broker.publish("t", "x")
    assert all(c.sent == [] for c in ch.values())


def test_preferences_changed_after_follow_take_effect():
    svc, broker, ch, _ = make_service()
    svc.follow("u1", "t")
    broker.publish("t", "1")
    svc.set_preferences("u1", ["sms"])
    broker.publish("t", "2")
    assert ch["email"].sent == [("u1", "1")]
    assert ch["sms"].sent == [("u1", "2")]


def test_mute_and_unmute():
    svc, broker, ch, _ = make_service()
    svc.follow("u1", "t")
    svc.mute("u1", "t")
    assert svc.is_muted("u1", "t") and not svc.is_muted("u1", "other")
    broker.publish("t", "quiet")
    assert ch["email"].sent == []
    svc.unmute("u1", "t")
    broker.publish("t", "loud")
    assert ch["email"].sent == [("u1", "loud")]


def test_follow_twice_delivers_once():
    svc, broker, ch, _ = make_service()
    svc.follow("u1", "t")
    svc.follow("u1", "t")
    broker.publish("t", "x")
    assert len(ch["email"].sent) == 1


def test_unfollow():
    svc, broker, ch, _ = make_service()
    svc.follow("u1", "t")
    assert svc.unfollow("u1", "t") is True
    assert svc.unfollow("u1", "t") is False
    broker.publish("t", "x")
    assert ch["email"].sent == []


def test_users_are_independent():
    svc, broker, ch, _ = make_service()
    svc.set_preferences("u2", ["sms"])
    svc.follow("u1", "t")
    svc.follow("u2", "t")
    svc.follow("u3", "other")
    broker.publish("t", "x")
    assert ch["email"].sent == [("u1", "x")]
    assert ch["sms"].sent == [("u2", "x")]


def test_channel_failure_is_retried_without_duplicating_other_channels():
    svc, broker, ch, sleeps = make_service(sms={"fail_times": 1})
    svc.set_preferences("u1", ["email", "sms"])
    svc.follow("u1", "t")
    broker.publish("t", "x")
    assert ch["email"].sent == [("u1", "x")]     # not duplicated by the retry
    assert ch["sms"].sent == [("u1", "x")]
    assert ch["sms"].calls == 2
    assert sleeps == [1.0]
    assert broker.dead_letters() == []


def test_permanently_failing_channel_dead_letters_but_earlier_channel_delivered():
    svc, broker, ch, sleeps = make_service(sms={"fail_times": 99})
    svc.set_preferences("u1", ["email", "sms"])
    svc.follow("u1", "t")
    broker.publish("t", "x")
    assert ch["email"].sent == [("u1", "x")]
    assert ch["sms"].calls == 3 and ch["sms"].sent == []
    (dl,) = broker.dead_letters()
    assert isinstance(dl.error, ChannelError)
    assert sleeps == [1.0, 2.0]


def test_one_users_failure_does_not_block_another_user():
    svc, broker, ch, _ = make_service(sms={"fail_times": 99})
    svc.set_preferences("u1", ["sms"])
    svc.follow("u1", "t")
    svc.follow("u2", "t")
    broker.publish("t", "x")
    assert ch["email"].sent == [("u2", "x")]


def test_each_message_tracked_separately_for_idempotency():
    svc, broker, ch, _ = make_service()
    svc.follow("u1", "t")
    broker.publish("t", "same")
    broker.publish("t", "same")                  # same payload, new message_id
    assert len(ch["email"].sent) == 2
