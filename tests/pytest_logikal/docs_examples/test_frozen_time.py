from datetime import datetime

from time_machine import Traveller


def test_frozen_time(frozen_time: Traveller) -> None:
    destination_time = datetime(2015, 10, 21, 16, 29, 42)
    frozen_time.move_to(destination_time)
    assert datetime.now() == destination_time
