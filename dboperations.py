from xmlrpc.client import Boolean

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging
from datetime import datetime

Base = declarative_base()
settings = {'db_url': 'sqlite:///changes.db'}

class DataChange(Base):

    __tablename__ = 'datachange'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    value = Column(String(250), nullable=False)
    timestamp = Column(String(250), nullable=False)


class CurrentValues(Base):

    __tablename__ = 'currentvalues'

    id = Column(Integer, primary_key=True)
    operator = Column(String)
    signal_q  = Column(Integer)
    reg_status = Column(Boolean)
    cipher_ind = Column(Boolean)
    kc = Column(String)
    kc_gprs = Column(String)
    cipher_key = Column(String)
    integrity_key = Column(String)
    tmsi = Column(String)
    tmsi_time = Column(Integer)
    lai = Column(String)
    ptmsi = Column(String)
    ptmsi_sign = Column(String)
    rai = Column(String)
    threshold = Column(Integer)
    phone_vendor = Column(String)
    phone_model = Column(String)
    firmware_version = Column(String)
    imei = Column(String)
    error = Column(String)
    timestamp = Column(DateTime)


class DbOperations():

    def __init__(self, settings):
        self.engine = create_engine(settings['db_url'], echo=False)
        Base.metadata.bind = self.engine

        self.dbsession = sessionmaker(bind=self.engine)
        self.session = self.dbsession()
        self.init_currentvalues()

    def init_currentvalues(self):
        if self.session.query(CurrentValues).count() == 0:
            cur_values = CurrentValues(id=1)
            self.session.add(cur_values)
            self.session.commit()


    def new_change(self, name, value, timestamp):
        new_change = DataChange(name=name, value=value, timestamp=timestamp)
        logging.info("Storing change (" + name + "," + value + "," + timestamp + ")")
        self.session.add(new_change)
        self.session.commit()
        pass


    def get_older_change(self):
        older_change = self.session.query(DataChange).order_by(DataChange.id).first()
        return older_change

    def get_older_change_rest(self):
        change = self.get_older_change()
        return change.id, {change.name : change.value , "timestamp" : change.timestamp }


    def close(self):
        self.session.close()


    def delete_change(self, id):
        # DataChange.query.filter_by(id=id).delete()
        logging.info("Deleting row " + str(id))
        self.session.query(DataChange).filter_by(id=id).delete()
        self.session.commit()

    def has_changes(self):
        return self.session.query(DataChange).count()

    def get_current_values(self):
        return self.session.query(CurrentValues)

    def different_value(self, field, value):
        current_values = self.session.query(CurrentValues).one()
        if getattr(current_values, field) != value:
            return True
        else:
            return False


    def update_current_value(self, field, value):
        self.session.query(CurrentValues).update({field: value, CurrentValues.timestamp: datetime.now()})
        self.session.commit()


def create_db(settings):
    engine = create_engine(settings['db_url'])
    Base.metadata.create_all(engine)


def insert_test(settings):
    dbo = DbOperations(settings)
    for i in range(10):
        si = str(i)
        dbo.new_change("name" + si, "value" + si, "2017-04-" + si)

    print("ROWS " + str(dbo.has_changes()))



def get_and_del_test(settings):
    dbo = DbOperations(settings)

    for i in range(10):
        change = dbo.get_older_change()
        print(str(change.id) + " " + change.name + " " + change.value + " " + change.timestamp)
        print("deleting " + str(change.id))
        dbo.delete_change(change.id)


if __name__ == '__main__':


    create_db(settings)
    #
    # insert_test(settings)

    get_and_del_test(settings)







