

from datetime import datetime
from datetime import timedelta
from datetime import time

from flask_restful import Resource
from sqlalchemy.sql import func

from ..models import MarketOrder

## THIS IS SUPPOSED TO BE OHLC, BUT NOT IMPLEMENTED CORRECTLY YET

def fetch_buy_or_sell_item_ohlc_stats(item_id, start, end):
    buystats = MarketOrder \
        .query \
        .filter(MarketOrder.ingest_time >= start) \
        .filter(MarketOrder.ingest_time < end) \
        .filter_by(item_id=item_id, is_buy_order=True) \
        .with_entities(
            func.avg(MarketOrder.price).label('low'),
            func.sum(MarketOrder.amount).label('total_volume')
        ).one()
    sellstats = MarketOrder \
        .query \
        .filter(MarketOrder.ingest_time >= start) \
        .filter(MarketOrder.ingest_time < end) \
        .filter_by(item_id=item_id, is_buy_order=False) \
        .with_entities(
            func.avg(MarketOrder.price).label('high'),
            func.sum(MarketOrder.amount).label('total_volume')
        ).one()
    sellopen = MarketOrder \
        .query \
        .filter(MarketOrder.ingest_time >= start) \
        .filter(MarketOrder.ingest_time < end) \
        .filter_by(item_id=item_id, is_buy_order=False) \
        .order_by(MarketOrder.ingest_time.asc()) \
        .first()
    sellclose = MarketOrder \
        .query \
        .filter(MarketOrder.ingest_time >= start) \
        .filter(MarketOrder.ingest_time < end) \
        .filter_by(item_id=item_id, is_buy_order=False) \
        .order_by(MarketOrder.ingest_time.desc()) \
        .first()
    return {
        'open_sell': float(sellopen.price if sellopen else 0),
        'sell_avg': float(sellstats.high if sellstats.high else 0),
        'buy_avg': float(buystats.low if buystats.low else 0),
        'close_sell': float(sellclose.price if sellclose else 0),
        'buy_volume' : float(buystats.total_volume if buystats.total_volume else 0),
        'sell_volume' : float(sellstats.total_volume if sellstats.total_volume else 0),
        'total_volume' : float(buystats.total_volume if buystats.total_volume else 0) + float(sellstats.total_volume if sellstats.total_volume else 0)
    }


def fetch_item_ohlc_stats(item_id):
    now = datetime.utcnow();
    count = 14
    ohlcdata = []
    ohlcdates = []
    ohlcends = []
    while(count >= 0):
        start = datetime.combine(datetime.utcnow() - timedelta(count), time.min)
        end = datetime.combine(datetime.utcnow() - timedelta(count), time.max)
        ohlcdates.append(start.strftime("%Y-%m-%d %H:%M:%S"))
        ohlcends.append(end.strftime("%Y-%m-%d %H:%M:%S"))
        ohlcdata.append(fetch_buy_or_sell_item_ohlc_stats(item_id,start, end))
        count = count - 1
        

    return {
        'dates': ohlcdates,
        'data': ohlcdata
    }


class OrdersStatsV1(Resource):
    def get(self, item_id):
        return fetch_item_ohlc_stats(item_id), 200
