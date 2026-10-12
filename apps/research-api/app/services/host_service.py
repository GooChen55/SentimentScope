from engines.contracts.dimensions import DIMENSIONS


class HostService:
    def __init__(self, research):
        self.research = research

    def start_host(self):
        return self.research.listener is not None

    def stop_host(self):
        if self.research.listener is not None:
            raise RuntimeError("主持人随研究任务运行，请取消研究任务以停止")

    def get_discussion_records(self, task_id=None):
        tasks = self.research.store.list()
        task_id = task_id or (tasks[0]["research_id"] if tasks else "")
        messages = [event["data"] for event in self.research.store.events(task_id) if event["event"] == "host_discussion_message"]
        names = {"insight": "Insight Engine", "media": "Media Engine", "host": "Host Agent"}
        return {"discussion_records": [{"speaker_name": names.get(m.get("source"), m.get("sender", "")),
                  "message_text": m.get("content", ""), "sent_at": m.get("timestamp", ""),
                  "dimension_key": m.get("section_key", "")} for m in messages]}

    def get_research_dimensions(self):
        return [{"key": key, "title": dimension.title, "index": str(index)} for index, (key, dimension) in enumerate(DIMENSIONS.items())]
