from taskiq.schedule_sources import LabelScheduleSource

from app.broker import broker

scheduler = LabelScheduleSource(broker)
