from datetime import datetime
import json
from sopp.window_finder import SuggestedReservation

class Tardys3Generator:

    def __init__(self,
                 chosen_reservation: SuggestedReservation,
                 chosen_reservation_end_time: datetime):
        self._chosen_reservation = chosen_reservation
        self._chosen_reservation_end_time = chosen_reservation_end_time

    def generate_tardys(self):

        # Input data from variables into json file
        reservation_in_tardys3 = {
            "transactionId": "c4c6f07b-e1a9-4a7c-a05e-09d186967e9b",
            "dateTimePublished": "2021-11-17T01:00:00.000Z",
            "dateTimeCreated": str(datetime.now().isoformat()),
            "checksum": "a35cf7d9",
            "scheduledEvents": [
                {"eventId": "c4c6f07b-e1a9-4a7c-a05e-09d186967e9b",
                 "dpaId": "ddda9e28-18e0-4ab7-9270-4f477045f32d",
                 "dpaName": self._chosen_reservation.ideal_reservation.facility.name,
                 "channels": ["4385ae93-5466-48d4-8024-14442193d783"],
                 "dateTimeStart": f"{self._chosen_reservation.suggested_start_time.isoformat()}",
                 "dateTimeEnd": f"{self._chosen_reservation_end_time.isoformat()}"}]
        }

        #print(json.dumps(tardys3, indent=4))
        print("Outputting tardys3 file as tardys3_reservation.json")
        with open("tardys3_reservation.json", "w") as fp:
            json.dump(reservation_in_tardys3, fp)
