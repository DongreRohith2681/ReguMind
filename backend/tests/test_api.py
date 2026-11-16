from fastapi.testclient import TestClient
from app.main import app

A={'states':['q0','q1'],'alphabet':['a'],'transitions':{'q0':{'a':'q1'},'q1':{'a':'q0'}},'start_state':'q0','accept_states':['q0'],'deterministic':True}
def test_health(): assert TestClient(app).get('/health').json()['status']=='ok'
def test_accept():
    c=TestClient(app); assert c.post('/api/accepts',json={'automaton':A,'word':['a','a']}).json()['accepted']
def test_determinize(): assert TestClient(app).post('/api/determinize',json=A).status_code==200
