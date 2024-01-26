from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola", "Burrata"]

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