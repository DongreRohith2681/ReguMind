from fastapi import APIRouter, HTTPException
from .models import *
from .automata import accepts, simulate, determinize, minimize, pta, rpni
from .data import generate, balanced_generate, split, features
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import base64
import pickle

router = APIRouter()

def _model(name, seed):
    if name == 'random_forest': return RandomForestClassifier(n_estimators=100, random_state=seed)
    if name == 'decision_tree': return DecisionTreeClassifier(random_state=seed)
    if name == 'logistic_regression': return LogisticRegression(max_iter=1000, random_state=seed)
    raise HTTPException(400, 'model must be logistic_regression, random_forest, or decision_tree')

@router.post('/accepts')
@router.post('/accept')
def check(r: WordRequest):
    try: return {'accepted': accepts(r.automaton, r.word), 'word': r.word}
    except ValueError as exc: raise HTTPException(422, str(exc))

@router.post('/simulate')
def simulation(r: WordRequest):
    try: return simulate(r.automaton, r.word)
    except ValueError as exc: raise HTTPException(422, str(exc))

@router.post('/determinize')
def det(a: Automaton): return determinize(a)

@router.post('/minimize')
def mini(a: Automaton): return minimize(a)

@router.post('/dataset')
def dataset(r: DatasetRequest):
    words, labels = balanced_generate(r.automaton, r.n_samples, r.max_length, r.seed)
    return {'words': words, 'labels': labels, 'positive_count': sum(labels), 'negative_count': len(labels) - sum(labels)}

@router.post('/train')
def train(r: TrainRequest):
    if len(r.words) != len(r.labels): raise HTTPException(400, 'words and labels must have matching lengths')
    if len(set(r.labels)) < 2: raise HTTPException(400, 'At least two classes are required')
    X, vocab = features(r.words); Xtr, Xte, ytr, yte = split(X, r.labels, r.test_size, r.seed)
    model = _model(r.model, r.seed); model.fit(Xtr, ytr); pred = model.predict(Xte)
    state = {'model': r.model, 'vocabulary': vocab, 'classes': model.classes_.tolist(), 'estimator': base64.b64encode(pickle.dumps(model)).decode('ascii')}
    return {'model': r.model, 'model_state': state, 'accuracy': float(accuracy_score(yte, pred)), 'precision': float(precision_score(yte, pred, zero_division=0)), 'recall': float(recall_score(yte, pred, zero_division=0)), 'f1': float(f1_score(yte, pred, zero_division=0)), 'confusion_matrix': confusion_matrix(yte, pred).tolist(), 'n_features': len(vocab) + 1, 'vocabulary': vocab}

@router.post('/predict')
def predict(r: PredictRequest):
    state = r.model_state; encoded = state.get('estimator')
    if encoded is None: raise HTTPException(400, 'model_state must come from train')
    try: estimator = pickle.loads(base64.b64decode(encoded))
    except Exception as exc: raise HTTPException(400, f'invalid model_state: {exc}')
    X, _ = features(r.words, state['vocabulary']); return {'predictions': estimator.predict(X).tolist()}

@router.post('/pta')
def build_pta(r: LearnRequest): return pta(r.positive, r.negative)

@router.post('/rpni')
def build_rpni(r: LearnRequest): return rpni(r.positive, r.negative)

@router.post('/learn')
def learn(r: LearnRequest): return rpni(r.positive, r.negative)
