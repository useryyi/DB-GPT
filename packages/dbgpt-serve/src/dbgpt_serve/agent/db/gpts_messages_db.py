import re
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    and_,
    desc,
    or_,
)

from dbgpt.agent.util.conv_utils import parse_conv_id
from dbgpt.storage.metadata import BaseDao, Model


class GptsMessagesEntity(Model):
    __tablename__ = "gpts_messages"
    id = Column(Integer, primary_key=True, comment="autoincrement id")

    conv_id = Column(
        String(255), nullable=False, comment="The unique id of the conversation record"
    )
    sender = Column(
        String(255),
        nullable=False,
        comment="Who speaking in the current conversation turn",
    )
    receiver = Column(
        String(255),
        nullable=False,
        comment="Who receive message in the current conversation turn",
    )
    model_name = Column(String(255), nullable=True, comment="message generate model")
    rounds = Column(Integer, nullable=False, comment="dialogue turns")
    is_success = Column(Boolean, default=True, nullable=True, comment="is success")
    app_code = Column(
        String(255),
        nullable=False,
        comment="The message in which app",
    )
    app_name = Column(
        String(255),
        nullable=False,
        comment="The message in which app name",
    )
    content = Column(
        Text(length=2**31 - 1), nullable=True, comment="Content of the speech"
    )
    current_goal = Column(
        Text, nullable=True, comment="The target corresponding to the current message"
    )
    context = Column(Text, nullable=True, comment="Current conversation context")
    review_info = Column(
        Text, nullable=True, comment="Current conversation review info"
    )
    action_report = Column(
        Text(length=2**31 - 1),
        nullable=True,
        comment="Current conversation action report",
    )
    resource_info = Column(
        Text,
        nullable=True,
        comment="Current conversation resource info",
    )
    role = Column(
        String(255), nullable=True, comment="The role of the current message content"
    )

    created_at = Column(DateTime, default=datetime.utcnow, comment="create time")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="last update time",
    )
    __table_args__ = (Index("idx_q_messages", "conv_id", "rounds", "sender"),)


class GptsMessagesDao(BaseDao):
    def append(self, entity: dict):
        session = self.get_raw_session()
        message = GptsMessagesEntity(
            conv_id=entity.get("conv_id"),
            sender=entity.get("sender"),
            receiver=entity.get("receiver"),
            content=entity.get("content"),
            is_success=entity.get("is_success", True),
            role=entity.get("role", None),
            model_name=entity.get("model_name", None),
            context=entity.get("context", None),
            rounds=entity.get("rounds", None),
            app_code=entity.get("app_code", None),
            app_name=entity.get("app_name", None),
            current_goal=entity.get("current_goal", None),
            review_info=entity.get("review_info", None),
            action_report=entity.get("action_report", None),
            resource_info=entity.get("resource_info", None),
        )
        session.add(message)
        session.commit()
        id = message.id
        session.close()
        return id

    def get_by_agent(
        self, conv_id: str, agent: str
    ) -> Optional[List[GptsMessagesEntity]]:
        session = self.get_raw_session()
        real_conv_id, _ = parse_conv_id(conv_id)
        gpts_messages = session.query(GptsMessagesEntity)
        if agent:
            gpts_messages = gpts_messages.filter(
                GptsMessagesEntity.conv_id.like(f"%{real_conv_id}%")
            ).filter(
                or_(
                    GptsMessagesEntity.sender == agent,
                    GptsMessagesEntity.receiver == agent,
                )
            )
        # Extract results first to apply custom sorting
        results = gpts_messages.all()

        # Custom sorting based on conv_id suffix and rounds
        def get_suffix_number(entity):
            suffix_match = re.search(r"_(\d+)$", entity.conv_id)
            if suffix_match:
                return int(suffix_match.group(1))
            return 0  # Default for entries without a numeric suffix

        # Sort first by numeric suffix, then by rounds
        sorted_results = sorted(results, key=lambda x: (get_suffix_number(x), x.rounds))
        session.close()
        return sorted_results

    def get_by_conv_id(self, conv_id: str) -> Optional[List[GptsMessagesEntity]]:
        session = self.get_raw_session()
        gpts_messages = session.query(GptsMessagesEntity)
        if conv_id:
            gpts_messages = gpts_messages.filter(GptsMessagesEntity.conv_id == conv_id)
        result = gpts_messages.order_by(GptsMessagesEntity.rounds).all()
        session.close()
        return result

    def get_between_agents(
        self,
        conv_id: str,
        agent1: str,
        agent2: str,
        current_goal: Optional[str] = None,
    ) -> Optional[List[GptsMessagesEntity]]:
        session = self.get_raw_session()
        gpts_messages = session.query(GptsMessagesEntity)
        if agent1 and agent2:
            gpts_messages = gpts_messages.filter(
                GptsMessagesEntity.conv_id == conv_id
            ).filter(
                or_(
                    and_(
                        GptsMessagesEntity.sender == agent1,
                        GptsMessagesEntity.receiver == agent2,
                    ),
                    and_(
                        GptsMessagesEntity.sender == agent2,
                        GptsMessagesEntity.receiver == agent1,
                    ),
                )
            )
        if current_goal:
            gpts_messages = gpts_messages.filter(
                GptsMessagesEntity.current_goal == current_goal
            )
        result = gpts_messages.order_by(GptsMessagesEntity.rounds).all()
        session.close()
        return result

    def get_last_message(self, conv_id: str) -> Optional[GptsMessagesEntity]:
        session = self.get_raw_session()
        gpts_messages = session.query(GptsMessagesEntity)
        if conv_id:
            gpts_messages = gpts_messages.filter(
                GptsMessagesEntity.conv_id == conv_id
            ).order_by(desc(GptsMessagesEntity.rounds))

        result = gpts_messages.first()
        session.close()
        return result

    def delete_chat_message(self, conv_id: str) -> bool:
        session = self.get_raw_session()
        gpts_messages = session.query(GptsMessagesEntity)
        gpts_messages.filter(GptsMessagesEntity.conv_id.like(f"%{conv_id}%")).delete()
        session.commit()
        session.close()
        return True
