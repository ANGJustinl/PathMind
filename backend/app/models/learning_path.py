from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union

# 修改关联表名称为path_content_associations，使其与content.py中引用的名称一致
path_content_association = Table(
    "path_content_associations",
    Base.metadata,
    Column("path_id", Integer, ForeignKey("learning_paths.id"), primary_key=True),
    Column("content_id", Integer, ForeignKey("learning_contents.id"), primary_key=True),
    Column("order_index", Integer, nullable=False),  # 内容在路径中的顺序
    Column("required", Boolean, default=True)  # 是否必修
)

class LearningPath(Base):
    """学习路径模型"""
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    subject = Column(String, nullable=False)
    difficulty_level = Column(Integer, default=2)  # 1-5级难度
    estimated_hours = Column(Float)  # 估计完成时间
    
    # 可包含路径设计图、前置要求、学习目标等
    path_metadata = Column(JSON)  # 修改列名为 path_metadata
    
    # 是否为系统自动生成的路径
    is_ai_generated = Column(Boolean, default=False)
    # 生成自适应路径的参数
    generation_parameters = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # 关系
    contents = relationship(
        "LearningContent", 
        secondary=path_content_association,
        order_by=path_content_association.c.order_index,
        back_populates="learning_paths"  # 添加这个以完成双向关系
    )
    author = relationship("User", foreign_keys=[created_by], back_populates="created_paths")
    enrollments = relationship("PathEnrollment", back_populates="learning_path")
    
    def __repr__(self):
        return f"<LearningPath {self.id}: {self.title}>"

class PathEnrollment(Base):
    """用户学习路径的注册和进度"""
    __tablename__ = "path_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    path_id = Column(Integer, ForeignKey("learning_paths.id"))
    
    # 整体进度 (0-100%)
    progress = Column(Float, default=0.0)
    # 详细进度记录
    content_progress = Column(JSON)
    
    # 学习时间记录
    total_study_time = Column(Float, default=0.0)  # 总学习时长(小时)
    study_sessions = Column(JSON, default=list)  # 学习会话记录 [{start_time, end_time, duration}]
    content_study_time = Column(JSON, default=dict)  # 每个内容的学习时间记录 {content_id: duration}
    
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    
    # 个性化设置
    personalization_settings = Column(JSON)
    
    # 关系
    user = relationship("User", back_populates="path_enrollments")
    learning_path = relationship("LearningPath", back_populates="enrollments")

class Resource(BaseModel):
    """学习资源模型"""
    title: str
    url: str
    type: str

class LearningPathNode(BaseModel):
    """学习路径节点模型"""
    id: str
    title: str
    description: str
    type: str = "topic"  # topic, project, milestone
    level: str = "初级"
    status: str = "未开始"  # 未开始, 进行中, 已完成
    resources: Optional[List[Resource]] = []
    
class PathConnection(BaseModel):
    """学习路径节点之间的连接"""
    source: str
    target: str

class LearningPathResponse(BaseModel):
    """学习路径API响应模型"""
    path_id: str
    title: str
    description: str
    estimated_duration: str = "3-6个月"
    nodes: List[LearningPathNode]
    connections: List[PathConnection]

class Video(BaseModel):
    """视频信息模型"""
    video_id: str
    title: str
    channel: str
    thumbnail: str
    
class VideoSearchRequest(BaseModel):
    """视频搜索请求模型"""
    query: str
    max_results: int = 5
    type: str = "video"
    
class VideoSearchResponse(BaseModel):
    """视频搜索响应模型"""
    videos: List[Video]

