# database.py
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime

# 数据库文件将保存在项目根目录，名为 aiv_memory.db
DATABASE_URL = "sqlite:///./aiv_memory.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 定义AI的状态和记忆模型
class AIStatus(Base):
    __tablename__ = "ai_status"

    id = Column(Integer, primary_key=True, index=True)
    # 当前状态: 'HOME' 或 'TRAVELING'
    current_state = Column(String, default='HOME')
    # 状态切换的计划时间
    next_event_time = Column(DateTime)
    # 上一次/当前的目的地
    location = Column(String, default='初始的小窝')
    # 下一次计划的目的地 (可能由用户建议)
    next_destination_plan = Column(String, nullable=True)
    # 最新的旅行日志
    latest_travel_log = Column(Text, nullable=True)

# 创建数据库和表
def init_db():
    Base.metadata.create_all(bind=engine)

    # 初始化数据，如果不存在的话
    db = SessionLocal()
    if db.query(AIStatus).count() == 0:
        initial_status = AIStatus(
            current_state='HOME',
            next_event_time=datetime.datetime.now() + datetime.timedelta(hours=1) # 假设1小时后出门
        )
        db.add(initial_status)
        db.commit()
    db.close()
