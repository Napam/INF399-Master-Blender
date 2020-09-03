import sqlite3 as db

def init(sqlite_file: str, *args, **kwargs):
    global __conn, c
    
    __conn = db.connect()
    c = __conn.cursor()

# import sqlalchemy as db 
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, Float
# 
# import blender_utils as utils
# 
# def init(sqlite_file: str, *args, **kwargs):
    # '''
    # Initializes database connection 
# 
    # '''
    # global __engine, __Base, __Session, session, Bbox
# 
    # __engine = db.create_engine(sqlite_file, *args, **kwargs)
    # __Base = declarative_base()
    # __Session = sessionmaker(bind=__engine)
    # session = __Session()
# 
    # class Bbox(__Base):
        # __tablename__ = 'bboxes'
# 
        # id = Column(Integer, primary_key=True)
        # imgid = Column(Integer)
        # class_ = Column(Integer)
        # p1 = Column(Float(4)) 
        # p2 = Column(Float(4))
        # p3 = Column(Float(4))
        # p4 = Column(Float(4))
        # p5 = Column(Float(4))
        # p6 = Column(Float(4))
        # p7 = Column(Float(4))
        # p8 = Column(Float(4))
    # 
    # __Base.metadata.create_all(__engine)
# 
# def get_engine():
    # return __engine



p1 FLOAT(4) NOT NULL,
p2 FLOAT(4) NOT NULL,
p3 FLOAT(4) NOT NULL,
p4 FLOAT(4) NOT NULL,
p5 FLOAT(4) NOT NULL,
p6 FLOAT(4) NOT NULL,
p7 FLOAT(4) NOT NULL,
p8 FLOAT(4) NOT NULL,

