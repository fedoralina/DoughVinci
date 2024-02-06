from typing import Text, List, Any, Dict
import logging
from rasa_sdk import Tracker, FormValidationAction, ValidationAction, Action
from rasa_sdk.events import EventType, SlotSet, FollowupAction, AllSlotsReset, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

ALLOWED_PIZZA_SIZES = ["small", "medium", "large", "family-size"]
ALLOWED_PIZZA_TYPES = ["Margherita", "Funghi", "Prosciutto", "Vegetariana", "Diavola"]
ALLOWED_DOUGH_TYPES = ["classic", "gluten-free", "garlic", "whole wheat"]
ALLOWED_NUM_PEOPLE = ["2","3","4","5","6"]
ALLOWED_BOOKING_TIME = ["19:00", "19:30", "20:00", "20:30", "21:00"]
ALLOWED_SITTING_OPTIONS = ["inside", "outside"]
ALLOWED_DRINKS_TYPES = ["Cola", "Water", "Icetea"]
ALLOWED_DRINKS_SIZES = ["300ml", "500ml", "300", "500"]
ALLOWED_ICE_OPTIONS = ["ice", "no ice"]
PIZZA_DRINK_MAPPINGS = {"Margherita": "Basil Breeze",
                        "Funghi": "Forest Frost", 
                        "Prosciutto": "Ham Harmony", 
                        "Vegetariana": "Pepper Passion", 
                        "Diavola": "Spicy Sip" }

class SharedVariables:
    table_booking_changed = False
    pizza_order_changed = False
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
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        try: 
            user_intent = tracker.latest_message.get('intent')['name']

            ## table booking
            if user_intent == 'change_table_booking' and SharedVariables.pizza_order_changed == False:
                # extract my relevant entities to avoid duckling entities like number
                user_entities = tracker.latest_message.get('entities')
                
                for i in range(len(user_entities)):
                    user_entity_name = user_entities[i]['entity']
                    user_entity_value = user_entities[i]['value']
                
                    if user_entity_name == 'pizza_type':  
                        SharedVariables.pizza_order_changed = True              
                        return[SlotSet("pizza_type", user_entity_value)]

                    if user_entity_name == 'pizza_size':
                        SharedVariables.pizza_order_changed = True
                        return[SlotSet("pizza_size", user_entity_value)]

            ## change order
            if user_intent == 'change_pizza_order' and SharedVariables.table_booking_changed == False:
            # extract my relevant entities to avoid duckling entities like number
                user_entities = tracker.latest_message.get('entities')
                
                for i in range(len(user_entities)):
                    user_entity_name = user_entities[i]['entity']
                    user_entity_value = user_entities[i]['value']
                    
                    # pizza amount is not changeable so easily in this config
                    
                    if user_entity_name == 'pizza_type':
                        SharedVariables.table_booking_changed = True
                        return[SlotSet("pizza_type", user_entity_value)]                    
                    
                    if user_entity_name == 'pizza_size':
                        SharedVariables.table_booking_changed = True
                        return[SlotSet("pizza_size", user_entity_value)]                        
            
            ## pizza order 
            if user_intent == 'inform_pizza_order':
                user_message = tracker.latest_message.get('text')
                # trigger logic to make user order one by one
                if " and " in user_message:
                    # deactivate loop to not just continue again, use action_listen to continue with user input after utterance of information
                    dispatcher.utter_message(response="utter_do_one_by_one")
                    SharedVariables.multiple_orders = True
                    SharedVariables.continue_after_multiple_orders = True
                    # reset this flag so amount can be set properly in single order
                    SharedVariables.is_pizza_amount_number_set = False
                    return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), SlotSet("pizza_amount", None), SlotSet("dough")]
                
                # set default pizza_amount to 1, otherwise to the extracted value to not ask user anytime for the amount
                elif SharedVariables.is_pizza_amount_number_set == False:  
                    for i in tracker.latest_message.get('entities'):
                        if i["entity"] == "number":
                            SharedVariables.is_pizza_amount_number_set = True
                            SharedVariables.pizza_amount = i['value']

                            return[SlotSet("pizza_amount", SharedVariables.pizza_amount)]

                        if (i["entity"] == "pizza_type" and i["value"] != None) or (i["entity"] == "pizza_size" and i["value"] != None) or (i["entity"] == "pizza_amount" and i["value"] == None):
                            SharedVariables.is_pizza_amount_number_set = False  
                            SharedVariables.pizza_amount = 1

                            return[SlotSet("pizza_amount", SharedVariables.pizza_amount)]

            
        except IndexError as e:
            logging.error(f"{__class__} {DoughVinciSlotChanger.run.__name__} - Error: {e}")
        
class ValidateDrinksForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_drinks_form"

    def validate_drinks_size(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `drinks_size` value."""
        
        if slot_value not in ALLOWED_DRINKS_SIZES:
            dispatcher.utter_message(text=f"Please choose between our sizes 300ml and 500ml. Which size do you want?")
            return {"drinks_size": None}
        dispatcher.utter_message(text=f"OK! I added your drink with size {slot_value}ml.")
        return {"drinks_size": slot_value}
    
    def validate_drinks_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `drinks_type` value."""
        if slot_value not in ALLOWED_DRINKS_TYPES:
            dispatcher.utter_message(text=f"Please choose between Cola, Water and our special Icetea. What drink do you want?")
            return {"drinks_type": None}
        
        users_pizza = tracker.get_slot('total_order')['1']['pizza_type']
        drinks_type = PIZZA_DRINK_MAPPINGS[users_pizza]
        
        dispatcher.utter_message(text=f"OK! For your {users_pizza} we have our special selfmade icetea '{drinks_type}'.")
        return {"drinks_type": drinks_type}
        
    
    def validate_drinks_ice(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `drinks_ice` value."""
        if slot_value not in ALLOWED_ICE_OPTIONS:
            dispatcher.utter_message(text=f"Please tell me if you want to have ice or no ice in your drink.")
            return {"drinks_ice": None}
        dispatcher.utter_message(text=f"OK! Your drink will be with {slot_value}.")
        return {"drinks_ice": slot_value}

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
                if slot_value is not None:
                    if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
                        dispatcher.utter_message(text=f"I could not recognize your wished size. You can choose from the following: {', '.join(ALLOWED_PIZZA_SIZES)}.")
                        return {"pizza_size": None}
                    
                    if SharedVariables.pizza_order_changed == True:
                        dispatcher.utter_message(text=f"Alright! I changed your pizza size to '{slot_value}'!")
                        SharedVariables.pizza_order_changed = False
                    
                    return {"pizza_size": slot_value}
                else:
                    SharedVariables.is_pizza_amount_number_set = False
                    return {"pizza_size": None}
            except AttributeError as e:
                logging.error(f'{__class__} {ValidatePizzaOrderForm.validate_pizza_size.__name__} - Error: {e}')

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
                if slot_value is not None:    

                    if SharedVariables.pizza_order_changed == True:
                        dispatcher.utter_message(text=f"Sure! I changed your pizza type to '{slot_value}'.")
                        SharedVariables.pizza_order_changed = False
                        return {"pizza_type", slot_value}
                    # lowercase strings to compare
                    standardized_types = [pizza_type.lower() for pizza_type in ALLOWED_PIZZA_TYPES]

                    if isinstance(slot_value, str) and slot_value.lower() in standardized_types:
                        # validation succeeded, set the value of the "cuisine" slot to value
                        return {"pizza_type": slot_value}
                    else:
                        dispatcher.utter_message(text=f"Unfortunately we do not offer this pizza type. We serve {', '.join(ALLOWED_PIZZA_TYPES)}.")
                        return {"pizza_type": None}
                else:
                    return {"pizza_type": None}
            except AttributeError as e:
                logging.error(f'{__class__} {ValidatePizzaOrderForm.validate_pizza_type.__name__} - Error: {e}')

    def validate_pizza_amount(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        return {"pizza_amount": SharedVariables.pizza_amount}
    

    def validate_dough(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        if SharedVariables.multiple_orders == True and SharedVariables.continue_after_multiple_orders == False:
            return {"dough": None}
        else:        
            try:
                if slot_value is not None:
                    if isinstance(slot_value, str) and slot_value in ALLOWED_DOUGH_TYPES:
                        return {"dough": slot_value}
                    else:
                        dispatcher.utter_message(text=f"Unfortunately we do not offer {slot_value} dough type. We serve {', '.join(ALLOWED_DOUGH_TYPES)}.")
                        return {"dough": None}
                else:
                    return {"dough": None}
            except AttributeError as e:
                logging.error(f'{__class__} {ValidatePizzaOrderForm.validate_dough.__name__} - Error: {e}')

class ActionTotalOrderAdd(Action):
    order_str = ""
    def name(self):
        return 'action_total_order_add'
    
    # get order elements in spoken form
    def print_order(self, order):
        order_elements = []
        total_orders = len(order)
        
        for index, (_, pizza) in enumerate(order.items(), 1):
            
            pizza_amount = pizza["pizza_amount"]

            # save order differently depending on pizza_amount
            if pizza_amount == 1 or pizza_amount == None:
                pizza_info = f"{num_to_word(1)} {pizza['pizza_size']} {pizza['pizza_type']} with {pizza['dough']} dough"
            elif pizza_amount > 1:
                pizza_info = f"{num_to_word(pizza_amount)} {pizza['pizza_size']} {pizza['pizza_type']} pizzas with {pizza['dough']} dough"
            
            if total_orders == 1:
                order_elements.append(pizza_info)
                order_elements.append(f"and a {pizza['drinks_type']}({pizza['drinks_size']}ml) with {pizza['drinks_ice']}")
            elif index < total_orders:
                order_elements.append(pizza_info + ",")
            else:
                order_elements.append("and " + pizza_info)
            
            self.order_str = " ".join(order_elements)
    
    def run(self, dispatcher, tracker, domain):
        pizza_type = tracker.get_slot("pizza_type")
        pizza_size = tracker.get_slot("pizza_size")
        pizza_amount = tracker.get_slot("pizza_amount")
        dough_type = tracker.get_slot("dough")

        drinks_type = tracker.get_slot("drinks_type")
        drinks_size = tracker.get_slot("drinks_size")
        drinks_ice = tracker.get_slot("drinks_ice")

        # safe order structured in a dict
        total_order_dict = tracker.get_slot("total_order")

        if total_order_dict is None:
            # dictionary never used
            total_order_dict = {}
        
        # atm: drinks recommendation only for single orders
        if drinks_type is not None:
            total_order_dict['1'].update({"drinks_type": drinks_type, "drinks_size": drinks_size, "drinks_ice": drinks_ice})
            self.print_order(total_order_dict)
            return[SlotSet("total_order", total_order_dict), SlotSet("order_readable", self.order_str)]

        order_key = len(total_order_dict) + 1
        if pizza_amount is None:
            pizza_amount = 1
        total_order_dict[order_key] = {"pizza_size": pizza_size, "pizza_type": pizza_type, "pizza_amount": pizza_amount, "dough": dough_type}

        # save order differently depending on pizza_amount
        if pizza_amount == 1:
            dispatcher.utter_message(f"Good choice! I will add {num_to_word(pizza_amount)} {pizza_size} {pizza_type} with {dough_type} dough to your order.")
        elif pizza_amount > 1:
            dispatcher.utter_message(f"Good choice! I will add {num_to_word(pizza_amount)} {pizza_size} {pizza_type} pizzas with {dough_type} dough to your order.")
        
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
            dispatcher.utter_message(text=f"I'm sorry that's not possible. Please be aware: We only offer tables from 2 to 6 people. For how many people you want me to reserve?")
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
            dispatcher.utter_message(text=f"OK! On {date} at {time} p.m. we have a free table.")
        else:
            dispatcher.utter_message(text=f"Got it! I changed the reservation time to {date} at {time} p.m.!")
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

class OrderInformation(Action):

    def name(self):
        return "action_order_information"
    
    def run(self, dispatcher, tracker, domain):
        order_readable = tracker.get_slot("order_readable")

        if order_readable is None:
            dispatcher.utter_message("You didn't finish your order, therefore I cannot summarize it.")
        else:
            dispatcher.utter_message(f"For now your order includes {order_readable}. Is there anything else I can do?")

class DoughTypeInformation(Action):
    def name(self):
        return "action_dough_information"
    
    def run(self, dispatcher, tracker, domain):
        # not available, reset set slot again
        dough_inform = tracker.get_slot("dough_inform")
        pizza_type = tracker.get_slot("pizza_type")

        if dough_inform in ALLOWED_DOUGH_TYPES:
            dispatcher.utter_message(text=f"Yes, we offer it! I will add the {dough_inform} dough for your {pizza_type}.")
            return [SlotSet("dough", dough_inform)]
        elif dough_inform not in ALLOWED_DOUGH_TYPES and dough_inform is not None:
            dispatcher.utter_message(text=f"I am sorry, we do not offer {dough_inform} as dough type. Please choose one of the following ones: {', '.join(ALLOWED_DOUGH_TYPES)}. ")
            # unset dough type again to trigger form
            return[SlotSet("dough_inform", None)]
        else:
            dispatcher.utter_message(text=f"We offer {', '.join(ALLOWED_DOUGH_TYPES)}.")

class ActionResetAllSlots(Action):

    def name(self):
        return "action_reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        return [AllSlotsReset()]
    
class ResetSlots(Action):
    def name(self):
        return 'action_reset_slots'
    
    def run(self, dispatcher, tracker, domain):
        # remove existing pizza_type and pizza_size slots
        return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), SlotSet("pizza_amount", None), SlotSet("dough", None), SlotSet("dough_inform",None)]
