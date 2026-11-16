from collections import deque
from .models import Automaton

EPSILON = {'', 'ε', 'epsilon'}

def _norm(a):
    return Automaton.model_validate(a) if isinstance(a, dict) else a

def _targets(a, state, symbol):
    value = a.transitions.get(state, {}).get(symbol, [])
    return {value} if isinstance(value, str) else set(value)

def epsilon_closure(a, states):
    closure = set(states)
    stack = list(closure)
    while stack:
        state = stack.pop()
        for symbol in EPSILON:
            for target in _targets(a, state, symbol):
                if target not in closure:
                    closure.add(target)
                    stack.append(target)
    return closure

def accepts(a, word):
    a = _norm(a)
    if any(symbol not in a.alphabet for symbol in word):
        raise ValueError('word contains symbols outside the automaton alphabet')
    current = epsilon_closure(a, {a.start_state})
    for symbol in word:
        current = epsilon_closure(a, {target for state in current for target in _targets(a, state, symbol)})
        if not current:
            return False
    return bool(current & a.accept_states)

def simulate(a, word):
    a = _norm(a)
    current = epsilon_closure(a, {a.start_state})
    path = [sorted(current)]
    for symbol in word:
        current = epsilon_closure(a, {t for s in current for t in _targets(a, s, symbol)})
        path.append(sorted(current))
    return {'accepted': bool(current & a.accept_states), 'path': path}

def determinize(a):
    a = _norm(a)
    start = frozenset(epsilon_closure(a, {a.start_state}))
    names = {start: '{' + ','.join(sorted(start)) + '}'}
    queue = deque([start]); transitions = {}
    while queue:
        subset = queue.popleft(); name = names[subset]; transitions[name] = {}
        for symbol in a.alphabet:
            target = frozenset(epsilon_closure(a, {t for s in subset for t in _targets(a, s, symbol)}))
            if not target:
                continue
            if target not in names:
                names[target] = '{' + ','.join(sorted(target)) + '}'; queue.append(target)
            transitions[name][symbol] = names[target]
    return Automaton(states=list(names.values()), alphabet=list(a.alphabet), transitions=transitions,
                     start_state=names[start], accept_states={n for s, n in names.items() if s & a.accept_states}, deterministic=True)

def _reachable(a):
    seen = {a.start_state}; stack = [a.start_state]
    while stack:
        state = stack.pop()
        for target in a.transitions.get(state, {}).values():
            if isinstance(target, list):
                stack.extend(target)
            elif target not in seen:
                seen.add(target); stack.append(target)
    return seen

def minimize(a):
    a = determinize(a)
    reachable = _reachable(a)
    states = sorted(reachable); accepting = set(a.accept_states) & reachable
    groups = [accepting, set(states) - accepting]; groups = [g for g in groups if g]
    changed = True
    while changed:
        changed = False; index = {s: i for i, g in enumerate(groups) for s in g}; new = []
        for group in groups:
            buckets = {}
            for state in group:
                signature = tuple(index.get(a.transitions.get(state, {}).get(symbol), -1) for symbol in a.alphabet)
                buckets.setdefault(signature, set()).add(state)
            new.extend(buckets.values()); changed |= len(buckets) > 1
        groups = new
    mapping = {state: f'q{i}' for i, group in enumerate(groups) for state in group}
    transitions = {f'q{i}': {s: mapping[t] for s, t in a.transitions.get(next(iter(group)), {}).items()} for i, group in enumerate(groups)}
    return Automaton(states=list(mapping.values()), alphabet=list(a.alphabet), transitions=transitions,
                     start_state=mapping[a.start_state], accept_states={mapping[s] for s in accepting}, deterministic=True)

def pta(positive, negative=None):
    negative = negative or []; states = ['q0']; transitions = {}; accepting = set(); rejecting = set()
    alphabet = sorted({symbol for word in positive + negative for symbol in word})
    for word, label in [(w, True) for w in positive] + [(w, False) for w in negative]:
        current = 'q0'
        for symbol in word:
            target = transitions.setdefault(current, {}).get(symbol)
            if target is None:
                target = f'q{len(states)}'; states.append(target); transitions[current][symbol] = target
            current = target
        (accepting if label else rejecting).add(current)
    if accepting & rejecting:
        raise ValueError('inconsistent positive and negative samples')
    return Automaton(states=states, alphabet=alphabet, transitions=transitions, start_state='q0', accept_states=accepting, deterministic=True)

def rpni(positive, negative):
    automaton = pta(positive, negative)
    groups = [{s} for s in automaton.states]
    def compatible(a, b):
        if (a in automaton.accept_states) != (b in automaton.accept_states): return False
        return True
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if compatible(next(iter(groups[i])), next(iter(groups[j]))):
                    merged = groups[i] | groups[j]; groups[i] = merged; groups.pop(j); changed = True; break
            if changed: break
    mapping = {s: f'q{i}' for i, g in enumerate(groups) for s in g}
    transitions = {f'q{i}': {symbol: mapping[target] for symbol, target in automaton.transitions.get(next(iter(g)), {}).items()} for i, g in enumerate(groups)}
    return Automaton(states=list(mapping.values()), alphabet=automaton.alphabet, transitions=transitions, start_state=mapping['q0'], accept_states={mapping[s] for s in automaton.accept_states}, deterministic=True)
