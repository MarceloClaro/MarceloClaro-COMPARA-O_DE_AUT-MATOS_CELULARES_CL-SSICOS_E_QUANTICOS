import itertools
import numpy as np
import pytest
from eca_qca_lab.adapters import BACKENDS,statevector
from eca_qca_lab.core import bits_from_index,fidelity,max_phase_aligned_error,oracle_statevector
@pytest.mark.integration
@pytest.mark.parametrize("backend",BACKENDS)
@pytest.mark.parametrize("rule",[30,60,90])
@pytest.mark.parametrize("sid",range(8))
def test_all_smoke_bases(backend,rule,sid):
 x=bits_from_index(sid,3);expected=oracle_statevector(rule,3,initial=x);actual=statevector(backend,rule,3,initial=x);assert fidelity(actual,expected)>=1-2e-7;np.testing.assert_allclose(abs(actual)**2,abs(expected)**2,atol=1e-12)
@pytest.mark.integration
@pytest.mark.parametrize("rule",[30,60,90])
def test_plus_pairs(rule):
 v={b:statevector(b,rule,3,plus_input=True) for b in BACKENDS}
 for a,b in itertools.combinations(BACKENDS,2):assert fidelity(v[a],v[b])>=1-2e-7;assert max_phase_aligned_error(v[a],v[b])<=2e-7
def test_unknown():
 with pytest.raises(ValueError):statevector("x",30,3,initial=(0,0,1))
