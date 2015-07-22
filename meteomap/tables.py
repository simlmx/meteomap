import sqlalchemy as sa
import geoalchemy2 as ga
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class City(Base):
    __tablename__ = 'city'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    region = sa.Column(sa.String(100), nullable=False)
    country = sa.Column(sa.String(100), nullable=False)
    location = sa.Column(ga.Geography(geometry_type='POINT', srid=4326))
    # total population (the smallest if there are multiple like
    # city/urban/metro, etc.)
    population = sa.Column(sa.Integer)
    # elevation in meters
    elevation = sa.Column(sa.Float)
    # (wikipedia) source
    source = sa.Column(sa.String(200))
    # This idea behind this thing is that when choosing what cities to show,
    # the cities with a smaller index will be chosen first
    # display_index = sa.Column(sa.Integer, default=1e9)
    # Index of the city in the region/country, when they are ordered by
    # decreasing population. It's for showing cities inteligently... at least
    # before I come up with a idea for a display_index
    region_index = sa.Column(sa.Integer, default=1e9)
    country_index = sa.Column(sa.Integer, default=1e9)


class MonthlyStat(Base):
    __tablename__ = 'monthly_stat'
    id = sa.Column(sa.Integer, primary_key=True)
    # 0 = jan, 11 = dec
    month = sa.Column(sa.Integer, nullable=False)
    city_id = sa.Column(sa.Integer, sa.ForeignKey("city.id"), nullable=False)
    stat_id = sa.Column(sa.Integer, sa.ForeignKey('stat.id'),
                     nullable=False)
    value = sa.Column(sa.Float, nullable=False)


class Stat(Base):
    __tablename__ = 'stat'
    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.String(20), nullable=False)
    name = sa.Column(sa.String(100), nullable=False)
    # unit symbol, e.g. mm or cm
    unit = sa.Column(sa.String(10), nullable=False)
    description = sa.Column(sa.String(250))
