from typing import Dict, List, Set, Union
from pydantic import BaseModel, Field, model_validator

Transition = Union[str, List[str]]

class Automaton(BaseModel):
    states: List[str]
    alphabet: List[str]
    transitions: Dict[str, Dict[str, Transition]] = Field(default_factory=dict)
    start_state: str
    accept_states: Set[str] = Field(default_factory=set)
    deterministic: bool = True

    @model_validator(mode='after')
    def validate_automaton(self):
        if len(set(self.states)) != len(self.states):
            raise ValueError('states must be unique')
        if len(set(self.alphabet)) != len(self.alphabet):
            raise ValueError('alphabet must be unique')
        state_set = set(self.states)
        if self.start_state not in state_set:
            raise ValueError('start_state must be in states')
        if not self.accept_states <= state_set:
            raise ValueError('accept_states must be in states')
        for source, mapping in self.transitions.items():
            if source not in state_set:
                raise ValueError(f'unknown transition source: {source}')
            for symbol, targets in mapping.items():
                if symbol not in self.alphabet and symbol not in {'', 'ε', 'epsilon'}:
                    raise ValueError(f'unknown symbol: {symbol}')
                values = [targets] if isinstance(targets, str) else targets
                if self.deterministic and len(values) > 1:
                    raise ValueError('deterministic transitions require one destination')
                if not all(target in state_set for target in values):
                    raise ValueError('transition destination must be in states')
        return self

class WordRequest(BaseModel):
    automaton: Automaton
    word: List[str] = Field(default_factory=list)

class DatasetRequest(BaseModel):
    automaton: Automaton
    n_samples: int = Field(100, ge=1, le=100000)
    max_length: int = Field(10, ge=0, le=1000)
    test_size: float = Field(.2, gt=0, lt=1)
    seed: int = 42

class TrainRequest(BaseModel):
    words: List[List[str]]
    labels: List[int]
    test_size: float = Field(.2, gt=0, lt=1)
    seed: int = 42
    model: str = 'logistic_regression'

class PredictRequest(BaseModel):
    words: List[List[str]]
    model_state: dict

class LearnRequest(BaseModel):
    positive: List[List[str]] = Field(default_factory=list)
    negative: List[List[str]] = Field(default_factory=list)
