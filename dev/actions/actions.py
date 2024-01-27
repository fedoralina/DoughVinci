from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola"]

ALLOWED_NUM_PEOPLE = [2,3,4,5,6,7,8]
ALLOWED_BOOKING_TIME = [700, 730, 800, 830, 900, 930, 1000]

class ValidatePizzaOrderForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_pizza_order_form"

    def validate_pizza_size(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `pizza_size` value."""

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f"I could not recognize your wished size. You can choose from the following: {', '.join(ALLOWED_PIZZA_SIZES)}.")
            return {"pizza_size": None}
        dispatcher.utter_message(text=f"OK! I will include a {slot_value} pizza to your order.")
        return {"pizza_size": slot_value}

    def validate_pizza_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `pizza_type` value."""
        
        # lowercase strings to compare
        standardized_types = [pizza_type.lower() for pizza_type in ALLOWED_PIZZA_TYPES]

        if slot_value.lower() not in standardized_types:
            dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {', '.join(ALLOWED_PIZZA_TYPES)}.")
            return {"pizza_type": None}
        #TODO: think about if needed to put bot message here
        dispatcher.utter_message(text=f"Alright, I will add a {slot_value} pizza.")
        return {"pizza_type": slot_value}
    
    #TODO: set validation for when both slots are set the same time

    #TODO: add list type as well, i.e. when user orders more than one pizza -> use list and isinstance

class ValidateTableBookingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_table_booking_form"

    def validate_num_people(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `num_people` value."""

        if slot_value not in ALLOWED_NUM_PEOPLE:
            dispatcher.utter_message(text=f"Please be aware: We only offer table from 2 to 8 people.")
            return {"num_people": None}
        dispatcher.utter_message(text=f"OK! I will reserve a table for {slot_value} people.")
        return {"num_people": slot_value}
    
    # TODO: validate booking time
    # TODO: validate inside outside
    # TODO: validate client name

    