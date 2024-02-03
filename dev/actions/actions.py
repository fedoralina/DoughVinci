from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import EventType, FollowupAction, SlotSet, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola"]

ALLOWED_NUM_PEOPLE = ["2","3","4","5","6"]
ALLOWED_BOOKING_TIME = ["7:00", "7:30", "8:00", "8:30", "9:00"]
ALLOWED_SITTING_OPTIONS = ["inside", "outside"]



class SharedVariables:
    table_booking_changed = False

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
    
    def run(self, dispatcher, tracker, domain):
        user_intent = tracker.latest_message.get('intent')['name']
        if user_intent == 'change_table_booking' and SharedVariables.table_booking_changed == False:
            return[ActiveLoop(None), FollowupAction("action_change_table_booking")]
        SharedVariables.table_booking_changed = False


    def validate_num_people(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `num_people` value."""

        if slot_value not in ALLOWED_NUM_PEOPLE:
            dispatcher.utter_message(text=f"I'm sorry that's not possible. Please be aware: We only offer table from 2 to 6 people. For how many people you want me to reserve?")
            return {"num_people": None}
        dispatcher.utter_message(text=f"OK! I will check for a table for {slot_value} people.")
        return {"num_people": slot_value}
    
    def validate_booking_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `booking_time` value."""

        if slot_value not in ALLOWED_BOOKING_TIME:
            dispatcher.utter_message(text=f"I'm sorry that's not possible. Please be aware: A table can ne booked only from 7pm to 9pm every half hour.")
            return {"booking_time": None}
        dispatcher.utter_message(text=f"Got it! For {slot_value} pm we have a free table.")
        return {"booking_time": slot_value}
    
    def validate_inside_outside(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `inside_outside` value."""

        if slot_value not in ALLOWED_SITTING_OPTIONS:
            dispatcher.utter_message(text=f"Please specify if you want to sit inside or outside.")
            return {"inside_outside": None}
        dispatcher.utter_message(text=f"Good choice! We have beautiful spots {slot_value}.")
        return {"inside_outside": slot_value}
    
    def validate_client_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `client_name` value."""

        if not isinstance(slot_value, str):
            dispatcher.utter_message(text=f"Please provide me your name for the reservation.")
            return {"client_name": None}
        dispatcher.utter_message(text=f"Thank you for your reservation, {slot_value}!.")
        return {"client_name": slot_value}
    
class ChangeTableBookingSlots(Action):
    def name(self):
        return 'action_change_table_booking'
    
    def run(self, dispatcher, tracker, domain):
        try:
            user_entity_name = tracker.latest_message.get('entities')[0]['entity']
            user_entity_value = tracker.latest_message.get('entities')[0]['value']
        except IndexError:
            return
        
        if user_entity_name == 'num_people':
            dispatcher.utter_message(text=f"Got it! I changed your reservation to a table for {user_entity_value} people!")
            SharedVariables.table_booking_changed = True
            return[SlotSet("num_people", user_entity_value), ActiveLoop("table_booking_form"), FollowupAction("table_booking_form")]
        
        if user_entity_name == 'booking_time':
            dispatcher.utter_message(text=f"Got it! I changed the reservation time to {user_entity_value} pm!")
            SharedVariables.table_booking_changed = True
            return[SlotSet("booking_time", user_entity_value), ActiveLoop("table_booking_form"), FollowupAction("table_booking_form")]
        
        if user_entity_name == 'inside_outside':
            dispatcher.utter_message(text=f"Got it! I changed your reservation to a table {user_entity_value}!")
            SharedVariables.table_booking_changed = True
            return[SlotSet("inside_outside", user_entity_value), ActiveLoop("table_booking_form"), FollowupAction("table_booking_form")]
         
