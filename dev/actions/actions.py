from typing import Text, List, Any, Dict
import logging
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola"]

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
        print("WIR ZIND JETZT TRINN")
        #if isinstance(slot_value, str):
        if slot_value.lower() in standardized_types:
            #dispatcher.utter_message(text=f"Alright, I will add a {slot_value} pizza.")
            # validation succeeded, set the value of the "cuisine" slot to value
            return {"pizza_type": slot_value}
        else:
            dispatcher.utter_message(text=f"Unfortunately we do not offer this pizza type. We serve {', '.join(ALLOWED_PIZZA_TYPES)}.")
            return {"pizza_type": None}
        # elif isinstance(slot_value, list):
        #     # TODO: check if each type exists
        #     # TODO: if yes: dann wird alles normal hinzugefügt
        #     # TODO: if no: sage, welcher wert nicht passt und frage, ob er es ersetzen möchte
        #     len_slot_val = len(slot_value)
        #     print(f"DAS HIER SIND SLOT_VALUES {slot_value}")
        #     if len_slot_val > 0:
        #         order_list = []
        #         for value in slot_value:
        #             if value.lower() in standardized_types:
        #                 # include value in slots
        #                 concatenated_slot = ", ".join(value)
        #                 order_list.append(value)
        #             else:
        #                 #TODO: hier muss dann die nachricht kommen, die die korrekten pizzatypen speichert, aber dem user die info gibt, dass es die bestimmte nicht gibt 
        #                 pass
        #         if len_slot_val != len(order_list):
        #             print("DIE LISTE IST NICHT VOLLSTÄNDIG!!")
        #             return {"pizza_type": None}
        #         return {"pizza_type": concatenated_slot}
        #     else:
		# 		# validation failed, set this slot to None so that the
		# 		# user will be asked for the slot again#
        #         return {"pizza_type": None}
        
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
        if pizza_size is None:
            pizza_size = "medium"

        # safe order structured in a dict
        total_order_dict = tracker.get_slot("total_order")

        # todo: er schreibt nicht die order hin sondern nur leeres dict
        if total_order_dict is None:
            # dictionary never used
            total_order_dict = {}

        print(f"{total_order_dict} is here")
        order_key = len(total_order_dict) + 1
        total_order_dict[order_key] = {"pizza_size": pizza_size, "pizza_type": pizza_type}
        
        print(f"{total_order_dict} is included")
        

        self.print_order(total_order_dict)
        #TODO: trigger here a message with the total order so far!! 
        dispatcher.utter_message(f"Your total order contains {self.order_str}.")
        
        return[SlotSet("total_order", total_order_dict), SlotSet("order_readable", self.order_str)]
    
class ResetSlots(Action):
    def name(self):
        return 'action_reset_slots'
    
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("Sure, tell me what you want to add.")
        # remove existing pizza_type and pizza_size slots
        return[SlotSet("pizza_type", None), SlotSet("pizza_size", None)]
