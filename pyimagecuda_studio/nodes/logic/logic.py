from dataclasses import dataclass
from typing import Annotated

from pyimagecuda import Image
from random import random

from ..constraints import FLOAT, TEXT, CHECKBOX
from ..node_merge import NodeMerge


@dataclass
class RandomOutNode(NodeMerge):
    input_1_probability: Annotated[float, FLOAT(min_value=0.0, max_value=1.0)] = 0.5

    def apply_merge(self, input_1: Image, input_2: Image) -> Image:
        print(f"[RANDOM OUT] {self.name} choosing between inputs (input_1: {self.input_1_probability*100}%, input_2: {(1-self.input_1_probability)*100}%)")
        if random() < self.input_1_probability:
            print(f"[RANDOM OUT] {self.name} selected input_1")
            return input_1
        else:
            print(f"[RANDOM OUT] {self.name} selected input_2")
            return input_2


code_example = """
import random

def condition():
    choice = random.choice([True, False])
    print(f"Random choice: {choice}")
    return choice
"""

@dataclass
class ConditionalNode(NodeMerge):
    code: Annotated[str, TEXT()] = code_example
    invert: Annotated[bool, CHECKBOX()] = False
    
    def apply_merge(self, input_1: Image, input_2: Image) -> Image:
        try:
            namespace = {'__builtins__': __builtins__}
            
            exec(self.code, namespace, namespace)
            
            if 'condition' not in namespace:
                raise ValueError("Function 'condition()' not found in code")
            
            result = namespace['condition']()
            
            if self.invert:
                result = not result
                print(f"[CONDITIONAL] {self.name} executed condition() → inverted to {result}")
            else:
                print(f"[CONDITIONAL] {self.name} executed condition() → {result}")
            
            if result:
                print(f"[CONDITIONAL] {self.name} True → selected input_1")
                return input_1
            else:
                print(f"[CONDITIONAL] {self.name} False → selected input_2")
                return input_2
                
        except Exception as e:
            print(f"[CONDITIONAL] {self.name} error: {e}")
            print(f"[CONDITIONAL] {self.name} defaulting to input_1")
            return input_1