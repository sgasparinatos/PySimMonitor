from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging

Base = declarative_base()

class DataChange(Base):

    __tablename__ = 'datachange'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    value = Column(String(250), nullable=False)
    timestamp = Column(String(250), nullable=False)


class DbOperations():

    def __init__(self, settings):
        self.engine = create_engine(settings['db_url'], echo=False)
        Base.metadata.bind = self.engine

        self.dbsession = sessionmaker(bind=self.engine)
        self.session = self.dbsession()


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

    settings = {'db_url': 'sqlite:///changes.db'}

    # create_db(settings)
    #
    # insert_test(settings)

    get_and_del_test(settings)







