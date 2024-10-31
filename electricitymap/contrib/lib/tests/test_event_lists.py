import logging
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import numpy as np

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey


class TestExchangeList(unittest.TestCase):
    def test_exchange_list(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        exchange_list.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        assert len(exchange_list.events) == 2

    def test_append_to_list_logs_error(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        with patch.object(exchange_list.logger, "error") as mock_error:
            exchange_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=1,
                source="trust.me",
            )
            mock_error.assert_called_once()

    def test_merge_exchanges(self):
        exchange_list_1 = ExchangeList(logging.Logger("test"))
        exchange_list_1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list_2 = ExchangeList(logging.Logger("test"))
        exchange_list_2.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=2,
            source="trust.me",
        )
        exchanges = ExchangeList.merge_exchanges(
            [exchange_list_1, exchange_list_2], logging.Logger("test")
        )
        assert len(exchanges) == 1
        assert exchanges.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert exchanges.events[0].netFlow == 3

    def test_merge_exchanges_with_none(self):
        exchange_list_1 = ExchangeList(logging.Logger("test"))
        exchange_list_1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list_2 = ExchangeList(logging.Logger("test"))
        exchange_list_2.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=np.nan,
            source="trust.me",
        )
        exchanges = ExchangeList.merge_exchanges(
            [exchange_list_1, exchange_list_2], logging.Logger("test")
        )
        assert len(exchanges) == 1
        assert exchanges.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert exchanges.events[0].netFlow == 1

    def test_merge_exchanges_with_negatives(self):
        exchange_list_1 = ExchangeList(logging.Logger("test"))
        exchange_list_1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list_2 = ExchangeList(logging.Logger("test"))
        exchange_list_2.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=-11,
            source="trust.me",
        )
        exchanges = ExchangeList.merge_exchanges(
            [exchange_list_1, exchange_list_2], logging.Logger("test")
        )
        assert len(exchanges) == 1
        assert exchanges.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert exchanges.events[0].netFlow == -10

    def test_update_exchange_list(self):
        exchange_list1 = ExchangeList(logging.Logger("test"))
        exchange_list1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list2 = ExchangeList(logging.Logger("test"))
        exchange_list2.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=2,
            source="trust.me",
        )
        updated_list = ExchangeList.update_exchanges(
            exchange_list1, exchange_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 2
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].netFlow == 2
        assert updated_list.events[0].source == "trust.me"
        assert updated_list.events[1].datetime == datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        assert updated_list.events[1].netFlow == 1
        assert updated_list.events[1].source == "trust.me"

    def test_update_exchange_list_with_different_zoneKey(self):
        exchange_list1 = ExchangeList(logging.Logger("test"))
        exchange_list1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list2 = ExchangeList(logging.Logger("test"))
        exchange_list2.append(
            zoneKey=ZoneKey("DE->DK-DK1"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=2,
            source="trust.me",
        )
        self.assertRaises(
            ValueError,
            ExchangeList.update_exchanges,
            exchange_list1,
            exchange_list2,
            logging.Logger("test"),
        )

    def test_update_exchange_list_with_longer_new_list(self):
        exchange_list1 = ExchangeList(logging.Logger("test"))
        exchange_list1.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list2 = ExchangeList(logging.Logger("test"))
        exchange_list2.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=2,
            source="trust.me",
        )
        exchange_list2.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            netFlow=3,
            source="trust.me",
        )
        updated_list = ExchangeList.update_exchanges(
            exchange_list1, exchange_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 2
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].netFlow == 2
        assert updated_list.events[0].source == "trust.me"
        assert updated_list.events[1].datetime == datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        assert updated_list.events[1].netFlow == 3
        assert updated_list.events[1].source == "trust.me"


class TestConsumptionList(unittest.TestCase):
    def test_consumption_list(self):
        consumption_list = TotalConsumptionList(logging.Logger("test"))
        consumption_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        consumption_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        assert len(consumption_list.events) == 2

    def test_append_to_list_logs_error(self):
        consumption_list = TotalConsumptionList(logging.Logger("test"))
        with patch.object(consumption_list.logger, "error") as mock_error:
            consumption_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=-1,
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestPriceList(unittest.TestCase):
    def test_price_list(self):
        price_list = PriceList(logging.Logger("test"))
        price_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=1,
            source="trust.me",
            currency="EUR",
        )
        assert len(price_list.events) == 1

    def test_append_to_list_logs_error(self):
        price_list = PriceList(logging.Logger("test"))
        with patch.object(price_list.logger, "error") as mock_error:
            price_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                price=1,
                source="trust.me",
                currency="EURO",
            )
            mock_error.assert_called_once()


class TestProductionBreakdownList(unittest.TestCase):
    def test_production_list(self):
        production_list = ProductionBreakdownList(logging.Logger("test"))
        production_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            source="trust.me",
        )
        assert len(production_list.events) == 1

    def test_production_list_logs_error(self):
        production_list = ProductionBreakdownList(logging.Logger("test"))
        with patch.object(production_list.logger, "error") as mock_error:
            production_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1),
                production=ProductionMix(wind=10),
                source="trust.me",
            )
            mock_error.assert_called_once()
        with patch.object(production_list.logger, "warning") as mock_warning:
            production_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                production=ProductionMix(wind=-10),
                source="trust.me",
            )
            mock_warning.assert_called_once()

    def test_merge_production_list_production_mix_only(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=11, coal=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=12, coal=2),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20),
            source="trust2.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=21, coal=1),
            source="trust2.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=22, coal=2),
            source="trust2.me",
        )
        production_list_3 = ProductionBreakdownList(logging.Logger("test"))
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=30),
            source="trust3.me",
        )
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=31, coal=1),
            source="trust3.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2, production_list_3],
            logging.Logger("test"),
        )
        assert len(merged.events) == 3
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].production is not None
        assert merged.events[0].production.wind == 60
        assert merged.events[0].production.coal is None
        assert merged.events[0].source == "trust.me, trust2.me, trust3.me"
        assert merged.events[0].zoneKey == ZoneKey("AT")
        assert merged.events[0].storage is None
        assert merged.events[0].sourceType == EventSourceType.measured

        assert merged.events[1].datetime == datetime(2023, 1, 2, tzinfo=timezone.utc)
        assert merged.events[1].production is not None
        assert merged.events[1].production.wind == 63
        assert merged.events[1].production.coal == 3

        assert merged.events[2].datetime == datetime(2023, 1, 3, tzinfo=timezone.utc)
        assert merged.events[2].production is not None
        assert merged.events[2].production.wind == 34
        assert merged.events[2].production.coal == 4

    def test_merge_production_list(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=11, coal=1),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=12, coal=2),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=21, coal=1),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=22, coal=2),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_3 = ProductionBreakdownList(logging.Logger("test"))
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=30),
            source="trust.me",
        )
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=31, coal=1),
            source="trust.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2, production_list_3],
            logging.Logger("test"),
        )
        assert len(merged.events) == 3
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].storage.hydro == 2

    def test_merge_production_list_doesnt_yield_extra_modes(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=None),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_mix = ProductionMix(wind=20)
        production_mix.add_value("hydro", None)
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=production_mix,
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2], logging.Logger("test")
        )
        assert len(merged.events) == 1
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].production.hydro is None
        assert merged.events[0].storage.battery is None
        merged_dict = merged.events[0].to_dict()
        assert merged_dict["production"].keys() == {"coal", "hydro", "wind"}
        assert merged_dict["storage"].keys() == {"hydro"}

    def test_merge_production_list_predicted(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            storage=StorageMix(hydro=1),
            source="trust.me",
            sourceType=EventSourceType.forecasted,
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=12, coal=2),
            source="trust.me",
            sourceType=EventSourceType.forecasted,
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
            sourceType=EventSourceType.forecasted,
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=22, coal=2),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
            sourceType=EventSourceType.forecasted,
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2],
            logging.Logger("test"),
        )
        assert len(merged.events) == 2
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].storage is not None
        assert merged.events[0].storage.hydro == 2
        assert merged.events[0].sourceType == EventSourceType.forecasted

    def test_merge_production_retains_corrected_negatives(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=-10, coal=10),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=-12, coal=12),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(hydro=20, coal=20),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(hydro=22, coal=22),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2],
            logging.Logger("test"),
        )
        assert len(merged.events) == 2
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].production is not None
        assert merged.events[0].production.wind is None
        assert merged.events[0].production.coal == 30
        assert merged.events[0].storage.hydro == 2
        assert merged.events[0].production._corrected_negative_values == {"wind"}

        assert merged.events[1].datetime == datetime(2023, 1, 3, tzinfo=timezone.utc)
        assert merged.events[1].production is not None
        assert merged.events[1].production.wind is None
        assert merged.events[1].production.coal == 34
        assert merged.events[1].storage.hydro == 2
        assert merged.events[1].production._corrected_negative_values == {"wind"}

    def test_merge_production_retains_corrected_negatives_with_0_and_none(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_mix_1 = ProductionMix(wind=-10, coal=10)
        production_mix_1.add_value("solar", -10, correct_negative_with_zero=True)
        production_mix_1.add_value("biomass", -10, correct_negative_with_zero=True)
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=production_mix_1,
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_mix_2 = ProductionMix(hydro=20, coal=20)
        production_mix_2.add_value("solar", 20, correct_negative_with_zero=True)
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=production_mix_2,
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2],
            logging.Logger("test"),
        )
        assert len(merged.events) == 1
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].production is not None
        assert merged.events[0].production.wind is None
        assert merged.events[0].production.solar == 20
        assert merged.events[0].production.coal == 30
        assert merged.events[0].production.biomass == 0
        assert merged.events[0].production._corrected_negative_values == {
            "wind",
            "solar",
            "biomass",
        }

    def test_update_production_list_with_production(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=11, coal=11),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20, coal=20),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 2
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].production.wind == 20
        assert updated_list.events[0].production.coal == 20
        assert updated_list.events[0].source == "trust.me"
        assert updated_list.events[1].datetime == datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        assert updated_list.events[1].production.wind == 11
        assert updated_list.events[1].production.coal == 11
        assert updated_list.events[1].source == "trust.me"

    def test_update_production_list_with_new_list_being_longer(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20, coal=20),
            source="trust.me",
        )
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=21, coal=21),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 2
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].production is not None
        assert updated_list.events[0].production.wind == 20
        assert updated_list.events[0].production.coal == 20
        assert updated_list.events[0].source == "trust.me"
        assert updated_list.events[1].datetime == datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        assert updated_list.events[1].production is not None
        assert updated_list.events[1].production.wind == 21
        assert updated_list.events[1].production.coal == 21
        assert updated_list.events[1].source == "trust.me"

    def test_update_storage_list_with_new_list_being_longer(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=2),
            source="trust.me",
        )
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            storage=StorageMix(hydro=3),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 2
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].storage is not None
        assert updated_list.events[0].storage.hydro == 2
        assert updated_list.events[0].source == "trust.me"
        assert updated_list.events[1].datetime == datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        assert updated_list.events[1].storage is not None
        assert updated_list.events[1].storage.hydro == 3
        assert updated_list.events[1].source == "trust.me"

    def test_update_production_list_with_storage(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            storage=StorageMix(hydro=2),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=2),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 2
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].storage is not None
        assert updated_list.events[0].storage.hydro == 2
        assert updated_list.events[0].source == "trust.me"
        assert updated_list.events[1].datetime == datetime(
            2023, 1, 2, tzinfo=timezone.utc
        )
        assert updated_list.events[1].storage is not None
        assert updated_list.events[1].storage.hydro == 2
        assert updated_list.events[1].source == "trust.me"

    def test_update_production_list_with_none_in_production(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=None, coal=20),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].production is not None
        assert updated_list.events[0].production.wind == 10
        assert updated_list.events[0].production.coal == 20
        assert updated_list.events[0].source == "trust.me"

    def test_update_production_list_with_none_in_storage(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=None),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].storage.hydro == 1
        assert updated_list.events[0].source == "trust.me"

    def test_update_production_with_different_zoneKey(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20, coal=20),
            source="trust.me",
        )
        self.assertRaises(
            ValueError,
            ProductionBreakdownList.update_production_breakdowns,
            production_list1,
            production_list2,
            logging.Logger("test"),
        )

    def test_update_production_with_different_source(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20, coal=20),
            source="trust.me.too",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].production is not None
        assert updated_list.events[0].production.wind == 20
        assert updated_list.events[0].production.coal == 20
        assert updated_list.events[0].source == ", ".join(
            set("trust.me, trust.me.too".split(", "))
        )

    def test_update_production_with_different_sourceType(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20, coal=20),
            source="trust.me",
            sourceType=EventSourceType.forecasted,
        )
        self.assertRaises(
            ValueError,
            ProductionBreakdownList.update_production_breakdowns,
            production_list1,
            production_list2,
            logging.Logger("test"),
        )

    def test_update_production_with_empty_list(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20, coal=20),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].production is not None
        assert updated_list.events[0].production.wind == 20
        assert updated_list.events[0].production.coal == 20
        assert updated_list.events[0].source == "trust.me"

    def test_update_production_with_empty_new_list(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10, coal=10),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].production is not None
        assert updated_list.events[0].production.wind == 10
        assert updated_list.events[0].production.coal == 10
        assert updated_list.events[0].source == "trust.me"

    def test_update_stroage_with_empty_list(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        production_list2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].storage is not None
        assert updated_list.events[0].storage.hydro == 1
        assert updated_list.events[0].source == "trust.me"

    def test_update_stroage_with_empty_new_list(self):
        production_list1 = ProductionBreakdownList(logging.Logger("test"))
        production_list1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list2 = ProductionBreakdownList(logging.Logger("test"))
        updated_list = ProductionBreakdownList.update_production_breakdowns(
            production_list1, production_list2, logging.Logger("test")
        )
        assert len(updated_list.events) == 1
        assert updated_list.events[0].datetime == datetime(
            2023, 1, 1, tzinfo=timezone.utc
        )
        assert updated_list.events[0].storage is not None
        assert updated_list.events[0].storage.hydro == 1
        assert updated_list.events[0].source == "trust.me"

    def test_filter_expected_modes(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=10,
                coal=None,
                solar=10,
                biomass=10,
                gas=10,
                unknown=10,
                hydro=10,
                oil=10,
            ),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=12, coal=12, solar=12, gas=12, unknown=12, hydro=12
            ),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 4, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=12, coal=12, solar=12, gas=12, unknown=12, hydro=12
            ),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        output = ProductionBreakdownList.filter_expected_modes(production_list_1)
        assert len(output.events) == 1
        assert output.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)

    def test_filter_expected_modes_none(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=10,
                coal=None,
                solar=None,
                biomass=10,
                gas=10,
                unknown=10,
                hydro=10,
                oil=10,
            ),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        output = ProductionBreakdownList.filter_expected_modes(production_list_1)
        assert len(output.events) == 0

    def test_filter_corrected_negatives(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=10,
                coal=None,
                solar=-10,
                biomass=10,
                gas=10,
                unknown=10,
                hydro=10,
                oil=10,
            ),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        output = ProductionBreakdownList.filter_expected_modes(production_list_1)
        assert len(output) == 1
        assert output.events[0].production.corrected_negative_modes == {"solar"}

    def test_not_strict_mode(self):
        production_list = ProductionBreakdownList(logging.Logger("test"))
        production_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=10,
                coal=None,
                solar=10,
                biomass=10,
                gas=10,
                unknown=10,
                hydro=10,
                oil=10,
            ),
            source="trust.me",
        )
        output = ProductionBreakdownList.filter_expected_modes(production_list)
        assert len(output) == 1

    def test_filter_by_passed_modes(self):
        production_list = ProductionBreakdownList(logging.Logger("test"))
        production_list.append(
            zoneKey=ZoneKey("US-NW-PGE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(
                wind=10,
                coal=None,
                solar=10,
                gas=10,
                unknown=10,
                hydro=10,
                oil=10,
            ),
            source="trust.me",
        )
        output = ProductionBreakdownList.filter_expected_modes(
            production_list, by_passed_modes=["biomass"]
        )
        assert len(output) == 1


class TestTotalProductionList(unittest.TestCase):
    def test_total_production_list(self):
        total_production = TotalProductionList(logging.Logger("test"))
        total_production.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        assert len(total_production.events) == 1


class TestListFeatures(unittest.TestCase):
    def test_df_representation(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_mix_1 = ProductionMix(wind=-10, coal=10)
        production_mix_1.add_value("solar", -10, correct_negative_with_zero=True)
        production_mix_1.add_value("biomass", -10, correct_negative_with_zero=True)
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=production_mix_1,
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=-12, coal=12),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        _test = production_list_1.dataframe  # TODO: Can this be removed?


print(type(ZoneKey("AT")))
