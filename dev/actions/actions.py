from typing import Text, List, Any, Dict
import logging
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import EventType, SlotSet, FollowupAction, AllSlotsReset, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola"]

class ValidatePizzaOrderForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_pizza_order_form"
    
    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get('text')

        #TODO: does user want to be asked "anything else" when bot says order one by one and user already made two orders?
        #TODO: so should we add another rule for this kind of flow or too complex?
        # trigger logic to make user order one by one
        if "and" in user_message:
            # deactivate loop to not just continue again, use action_listen to continue with user input after utterance of information
            dispatcher.utter_message(response="utter_do_one_by_one")
            return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), ActiveLoop(None), FollowupAction("action_listen")]

           
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
        #dispatcher.utter_message(text=f"OK! I will include a {slot_value} pizza to your order.")
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

        if isinstance(slot_value, str) and slot_value.lower() in standardized_types:
            #dispatcher.utter_message(text=f"Alright, I will add a {slot_value} pizza.")
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"pizza_type": slot_value}
        else:
            dispatcher.utter_message(text=f"Unfortunately we do not offer this pizza type. We serve {', '.join(ALLOWED_PIZZA_TYPES)}.")
            return {"pizza_type": None}
        
class ActionTotalOrderAdd(Action):
    order_str = ""
    def name(self):
        return 'action_total_order_add'
    
    # get order elements in spoken form
    def print_order(self, order):
        order_elements = []
        total_orders = len(order)
        
        for index, (_, pizza) in enumerate(order.items(), 1):
            pizza_info = f"{pizza['pizza_size']} {pizza['pizza_type']}"
            if total_orders == 1:
                order_elements.append(pizza_info)
            elif index < total_orders:
                order_elements.append(pizza_info + ",")
            else:
                order_elements.append("and " + pizza_info)
            
            self.order_str = " ".join(order_elements)
    
    def run(self, dispatcher, tracker, domain):
        pizza_type = tracker.get_slot("pizza_type")
        pizza_size = tracker.get_slot("pizza_size")
	    #pizza_amount = tracker.get_slot("pizza_amount")

        # safe order structured in a dict
        total_order_dict = tracker.get_slot("total_order")

        if total_order_dict is None:
            # dictionary never used
            total_order_dict = {}

        order_key = len(total_order_dict) + 1
        total_order_dict[order_key] = {"pizza_size": pizza_size, "pizza_type": pizza_type}
        
        self.print_order(total_order_dict)
        dispatcher.utter_message(f"Your total order contains {self.order_str}.")
        
        return[SlotSet("total_order", total_order_dict), SlotSet("order_readable", self.order_str)]

class ActionPizzaTypeInformation(Action):

    def name(self):
        return "action_pizza_type_information"
    
    def run(self, dispatcher, tracker, domain):
        # give information and trigger question again
        pizza_offer = ", ".join(pizza for pizza in ALLOWED_PIZZA_TYPES[:-1]) + ", and " + ALLOWED_PIZZA_TYPES[-1]
        dispatcher.utter_message(f"We offer {pizza_offer}.")
        return []
    
class ActionPizzaSizeInformation(Action):

    def name(self):
        return "action_pizza_size_information"
    
    def run(self, dispatcher, tracker, domain):
        # give information and trigger question again
        size_offer = ", ".join(size for size in ALLOWED_PIZZA_SIZES[:-1]) + ", and " + ALLOWED_PIZZA_SIZES[-1]
        dispatcher.utter_message(f"We offer {size_offer}.")
        return []


class ActionResetAllSlots(Action):

    def name(self):
        return "action_reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        return [AllSlotsReset()]
    
class ResetSlots(Action):
    def name(self):
        return 'action_reset_slots'
    
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("Sure, tell me what you want to add.")
        # remove existing pizza_type and pizza_size slots
        return[SlotSet("pizza_type", None), SlotSet("pizza_size", None)]
