"""LLD problem 07: pub-sub broker with retry + a notification service. Read lesson.md.

Dataclasses, ABCs and the exception are provided. Implement everything marked `...`.
No real sleeping anywhere: the broker takes an injected `sleeper(seconds)` callable.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


class ChannelError(Exception):
    """A notification channel failed to send."""


@dataclass(frozen=True)
class Message:
    """A published message. message_id is a broker-wide counter starting at 1."""
    message_id: int
    topic: str
    payload: str


@dataclass(frozen=True)
class DeadLetter:
    """A delivery that exhausted its retries.

    message: the Message; subscriber: the Subscriber object; attempts: how many
    times handle() was called (== max_attempts); error: the LAST exception raised.
    """
    message: Message
    subscriber: object
    attempts: int
    error: Exception


class Subscriber(ABC):
    """Abstract: handle(message) -> None. Raise any Exception to signal failure."""

    @abstractmethod
    def handle(self, message):
        ...


class PubSubBroker:
    """PubSubBroker(max_attempts=3, base_delay=1.0, sleeper=None). In-memory, synchronous.

    - max_attempts < 1 -> ValueError; base_delay < 0 -> ValueError.
    - sleeper: callable(seconds). Default time.sleep. The broker NEVER sleeps any
      other way.
    - subscribe(topic, subscriber): append to that topic's list. Subscribing the same
      subscriber object (==) to the same topic again is a no-op (idempotent).
    - unsubscribe(topic, subscriber) -> bool: True if it was subscribed, else False.
    - subscribers(topic) -> list: a COPY, in subscription order ([] if unknown topic).
    - publish(topic, payload) -> Message: creates Message(next_id, topic, payload)
      (ids 1, 2, 3, ...; a publish with no subscribers still consumes an id), then
      delivers it synchronously to a SNAPSHOT of the topic's subscribers, in
      subscription order. (Changes made to the subscriber list by a handler affect
      only later publishes.) Returns the Message.
    - Delivery of one message to one subscriber: call handle(message). If it raises an
      `Exception`, retry. Attempt k (k >= 1) that fails and is not the last is
      followed by sleeper(base_delay * 2 ** (k - 1)); no sleep after the final
      failure. After max_attempts failures append DeadLetter(message, subscriber,
      max_attempts, last_error) and move on to the next subscriber. publish never
      raises because of a subscriber failure. BaseException (KeyboardInterrupt, ...)
      is NOT caught.
    - dead_letters() -> list: a COPY, in the order they were created.
    - redrive_dead_letters() -> int: for each current dead letter, in order, run the
      same retry delivery again (same sleeps). Successful ones are removed; ones that
      fail again stay in the list unchanged. Returns the number that succeeded.
    """

    def __init__(self, max_attempts=3, base_delay=1.0, sleeper=None):
        ...

    def subscribe(self, topic, subscriber):
        ...

    def unsubscribe(self, topic, subscriber):
        ...

    def subscribers(self, topic):
        ...

    def publish(self, topic, payload):
        ...

    def dead_letters(self):
        ...

    def redrive_dead_letters(self):
        ...


class Channel(ABC):
    """Abstract delivery channel. Attribute `name` (str); send(user_id, text) -> None,
    raising ChannelError on failure."""

    @abstractmethod
    def send(self, user_id, text):
        ...


class FakeChannel(Channel):
    """FakeChannel(name, fail_times=0): in-memory test double.

    Attributes: name; sent (list of (user_id, text) for SUCCESSFUL sends only);
    calls (int, every send() call including failed ones).
    The first `fail_times` calls raise ChannelError (and are not added to `sent`);
    later calls succeed.
    """

    def __init__(self, name, fail_times=0):
        ...

    def send(self, user_id, text):
        ...


class EmailChannel(FakeChannel):
    """EmailChannel(fail_times=0): a FakeChannel named "email"."""

    def __init__(self, fail_times=0):
        ...


class SMSChannel(FakeChannel):
    """SMSChannel(fail_times=0): a FakeChannel named "sms"."""

    def __init__(self, fail_times=0):
        ...


class PushChannel(FakeChannel):
    """PushChannel(fail_times=0): a FakeChannel named "push"."""

    def __init__(self, fail_times=0):
        ...


class NotificationService:
    """NotificationService(broker, channels, default_channels=("email",)).

    channels: dict[str, Channel] keyed by channel name. Every name in
    default_channels must exist in `channels`, else ValueError.

    - set_preferences(user_id, channel_names): the ordered channels this user wants.
      Unknown channel name -> ValueError (state unchanged). [] means "no notifications".
    - preferences(user_id) -> list: the user's list, or list(default_channels).
    - mute(user_id, topic) / unmute(user_id, topic) / is_muted(user_id, topic) -> bool.
    - follow(user_id, topic): subscribe a per-(user, topic) Subscriber to the broker.
      Following twice is a no-op (exactly one delivery per publish).
    - unfollow(user_id, topic) -> bool: True if the user was following.
    - When a message is published on a followed topic, the user's subscriber looks up
      the CURRENT preferences and, unless the topic is muted, calls
      channel.send(user_id, message.payload) for each preferred channel in order.
    - If a channel raises, the subscriber's handle() must raise so the broker retries.
      On retry it must NOT re-send on channels that already succeeded for that
      message_id (idempotent per (message_id, channel)).
    """

    def __init__(self, broker, channels, default_channels=("email",)):
        ...

    def set_preferences(self, user_id, channel_names):
        ...

    def preferences(self, user_id):
        ...

    def mute(self, user_id, topic):
        ...

    def unmute(self, user_id, topic):
        ...

    def is_muted(self, user_id, topic):
        ...

    def follow(self, user_id, topic):
        ...

    def unfollow(self, user_id, topic):
        ...
