import sqlalchemy as sa
import geoalchemy2 as ga
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class City(Base):
    __tablename__ = 'city'
    id = sa.Column(sa.Integer, primary_key=True)

    location = sa.Column(ga.Geography(geometry_type='POINT', srid=4326))

    # total population (the smallest if there are multiple like
    # city/urban/metro, etc.)
    city_pop = sa.Column(sa.Integer)

    # elevation in meters
    elevation = sa.Column(sa.Float)


class MontlyStats(Base):
    __tablename__ = 'monthly_stats'
    id = sa.Column(sa.Integer, primary_key=True)
    Month = sa.Column(sa.Integer, nullable=False)
    sa.Column('city_id', sa.Integer, sa.ForeignKey("user.id"), nullable=False),
    avgMaxTemp = sa.Column(sa.Float)
    avgMinTemp = sa.Column(sa.Float)
