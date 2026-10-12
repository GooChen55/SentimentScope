from engines.common.eventing.bus import publish
from engines.common.eventing.event import EventType, RoleProgressEvent, RoleResultEvent, RoleErrorEvent, \
    SectionReadyEvent, HostDiscussionMessageEvent


def pub_role_progress(data: RoleProgressEvent):
    publish(event_type=EventType.ROLE_PROGRESS, data=data.model_dump())


def pub_role_result(data: RoleResultEvent):
    publish(event_type=EventType.ROLE_RESULT, data=data.model_dump())


def pub_role_error(data: RoleErrorEvent):
    publish(event_type=EventType.ROLE_ERROR, data=data.model_dump())


def publish_section_read_ready(event: SectionReadyEvent) -> None:
    publish(EventType.SECTION_READY, event.model_dump())


def publish_host_discussion_message(event: HostDiscussionMessageEvent) -> None:
    publish(EventType.HOST_DISCUSSION_MESSAGE, event.model_dump())
