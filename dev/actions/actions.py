from typing import Text, List, Any, Dict
import logging
from rasa_sdk import Tracker, FormValidationAction, ValidationAction, Action
from rasa_sdk.events import EventType, SlotSet, FollowupAction, AllSlotsReset, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola"]
ALLOWED_NUM_PEOPLE = ["2","3","4","5","6"]
ALLOWED_BOOKING_TIME = ["19:00", "19:30", "20:00", "20:30", "21:00"]
ALLOWED_SITTING_OPTIONS = ["inside", "outside"]

class SharedVariables:
    table_booking_changed = False
    is_pizza_amount_number_set = False
    multiple_orders = False
    continue_after_multiple_orders = False

    pizza_amount = 1

# convert small digits to words for human-like conversation
def num_to_word(num):
    if num == 1:
        return "one"
    elif num == 2:
        return "two"
    elif num == 3:
        return "three"
    else:
        return num

    
class DoughVinciSlotChanger(ValidationAction):
    # this is run before the Form Validation
    # TODO: prob. add async, in table booking it was used
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        try: 
            #TODO: does user want to be asked "anything else" when bot says order one by one and user already made two orders?
            #TODO: so should we add another rule for this kind of flow or too complex?
            user_intent = tracker.latest_message.get('intent')['name']

            ## table booking
            if user_intent == 'change_table_booking' and SharedVariables.table_booking_changed == False:
                user_entity_name = tracker.latest_message.get('entities')[0]['entity']
                user_entity_value = tracker.latest_message.get('entities')[0]['value']
                if user_entity_name == 'num_people':  
                    SharedVariables.table_booking_changed = True              
                    return[SlotSet("num_people", user_entity_value)]

                if user_entity_name == 'time':
                    SharedVariables.table_booking_changed = True
                    return[SlotSet("time", user_entity_value)]

                if user_entity_name == 'inside_outside':
                    SharedVariables.table_booking_changed = True
                    return[SlotSet("inside_outside", user_entity_value)]
            
            ## pizza order 
            if user_intent == 'inform_pizza_order':
                user_message = tracker.latest_message.get('text')
                # trigger logic to make user order one by one
                if "and" in user_message:
                    # deactivate loop to not just continue again, use action_listen to continue with user input after utterance of information
                    dispatcher.utter_message(response="utter_do_one_by_one")
                    SharedVariables.multiple_orders = True
                    SharedVariables.continue_after_multiple_orders = True
                    return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), SlotSet("pizza_amount", None)]
                
                # set default pizza_amount to 1, otherwise to the extracted value to not ask user anytime for the amount
                elif SharedVariables.is_pizza_amount_number_set == False: 
                    for i in tracker.latest_message.get('entities'):
                        if i["entity"] == "number":
                            SharedVariables.is_pizza_amount_number_set = True
                            SharedVariables.pizza_amount = i['value']

                            return[SlotSet("pizza_amount", SharedVariables.pizza_amount)]
                        elif (i["entity"] == "pizza_type" and i["value"] != None) or (i["entity"] == "pizza_amount" and i["value"] == None):
                            SharedVariables.is_pizza_amount_number_set = False  
                            SharedVariables.pizza_amount = 1

                            logging.info(f"DAS IST NUN IN ELIF")
                            return[SlotSet("pizza_amount", SharedVariables.pizza_amount)]
                         
        except IndexError as e:
            logging.error(f"{__class__} {__name__} - Error: {e}")
        

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
        
        if SharedVariables.multiple_orders == True and SharedVariables.continue_after_multiple_orders == False:
            return {"pizza_size": None}
        else:
            try:
                if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
                    dispatcher.utter_message(text=f"I could not recognize your wished size. You can choose from the following: {', '.join(ALLOWED_PIZZA_SIZES)}.")
                    return {"pizza_size": None}

                return {"pizza_size": slot_value}
            except AttributeError as e:
                logging.error(f'{__class__} {__name__} - Error: {e}')

    def validate_pizza_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `pizza_type` value."""

        if SharedVariables.multiple_orders == True and SharedVariables.continue_after_multiple_orders == False:
            return {"pizza_type": None}
        else:        
            try:
                # lowercase strings to compare
                standardized_types = [pizza_type.lower() for pizza_type in ALLOWED_PIZZA_TYPES]

                if isinstance(slot_value, str) and slot_value.lower() in standardized_types:
                    # validation succeeded, set the value of the "cuisine" slot to value
                    return {"pizza_type": slot_value}
                else:
                    dispatcher.utter_message(text=f"Unfortunately we do not offer this pizza type. We serve {', '.join(ALLOWED_PIZZA_TYPES)}.")
                    return {"pizza_type": None}
            except AttributeError as e:
                logging.error(f'{__class__} {__name__} - Error: {e}')

    def validate_pizza_amount(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
            
        return {"pizza_amount": SharedVariables.pizza_amount}

class ActionTotalOrderAdd(Action):
    order_str = ""
    def name(self):
        return 'action_total_order_add'
    
    # get order elements in spoken form
    def print_order(self, order):
        order_elements = []
        total_orders = len(order)
        
        for index, (_, pizza) in enumerate(order.items(), 1):
            pizza_info = f"{num_to_word(pizza['pizza_amount'])} {pizza['pizza_size']} {pizza['pizza_type']}"
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
        pizza_amount = tracker.get_slot("pizza_amount")

        # safe order structured in a dict
        total_order_dict = tracker.get_slot("total_order")

        if total_order_dict is None:
            # dictionary never used
            total_order_dict = {}
        
        order_key = len(total_order_dict) + 1
        total_order_dict[order_key] = {"pizza_size": pizza_size, "pizza_type": pizza_type, "pizza_amount": pizza_amount}
        
        self.print_order(total_order_dict)
        
        return[SlotSet("total_order", total_order_dict), SlotSet("order_readable", self.order_str)]


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
            dispatcher.utter_message(text=f"I'm sorry that's not possible. Please be aware: We only offer table from 2 to 6 people. For how many people you want me to reserve?")
            return {"num_people": None}                
        if SharedVariables.table_booking_changed == False: 
            dispatcher.utter_message(text=f"OK! I will check for a table for {slot_value} people.")
        else:
            dispatcher.utter_message(text=f"Got it! I changed your reservation to a table for {slot_value} people!")
            SharedVariables.table_booking_changed = False
        return {"num_people": slot_value}
    
    def validate_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `time` value."""
        date = slot_value[:10]
        time = slot_value[11:16]

        if time not in ALLOWED_BOOKING_TIME:
            dispatcher.utter_message(text=f"I'm sorry that's not possible. Please be aware: A table can ne booked only from 19:00 to 21:00 every half hour.")
            return {"date": None, "time": None}
        if SharedVariables.table_booking_changed == False: 
            dispatcher.utter_message(text=f"OK! On {date} at {time} we have a free table.")
        else:
            dispatcher.utter_message(text=f"Got it! I changed the reservation time to {date} at {time}!")
            SharedVariables.table_booking_changed = False
        return {"date": date, "time": time}
    
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
        if SharedVariables.table_booking_changed == False: 
            dispatcher.utter_message(text=f"Good choice! We have beautiful spots {slot_value}.")
        else:
            dispatcher.utter_message(text=f"Got it! I changed your reservation to a table {slot_value}!")
            SharedVariables.table_booking_changed = False
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
        # utter size details for size options 
        ADDITIONAL_SIZE_INFO = ["25 cm", "30 cm", "35 cm", "40 cm"]
        size_offer = ", ".join(f"{size} ({info})" for size, info in zip(ALLOWED_PIZZA_SIZES[:-1], ADDITIONAL_SIZE_INFO[:-1])) + ", and " + f"{ALLOWED_PIZZA_SIZES[-1]} ({ADDITIONAL_SIZE_INFO[-1]})"

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
        return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), SlotSet("pizza_amount", None)]

