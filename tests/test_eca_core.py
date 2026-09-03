import itertools
import numpy as np
import pytest
from eca_qca_lab.core import *

@pytest.mark.parametrize(("rule","bits"),[(30,"00011110"),(60,"00111100"),(90,"01011010")])
def test_truth(rule,bits):assert "".join(str(r[3]) for r in truth_table(rule))==bits
@pytest.mark.parametrize("rule",[30,60,90])
@pytest.mark.parametrize("address",range(8))
def test_local(rule,address):
 l,c,r=bits_from_index(address,3);assert wolfram_local(rule,l,c,r)==(rule>>address)&1
@pytest.mark.parametrize("width",range(1,9))
def test_index_roundtrip(width):
 for i in range(1<<width):assert index_from_bits(bits_from_index(i,width))==i
@pytest.mark.parametrize("rule",[30,60,90])
@pytest.mark.parametrize("sid",range(8))
def test_sync_periodic(rule,sid):
 x=bits_from_index(sid,3);assert eca_step(x,rule)==tuple(wolfram_local(rule,x[(i-1)%3],x[i],x[(i+1)%3]) for i in range(3))
@pytest.mark.parametrize("sid",range(8))
def test_rule90(sid):
 x=bits_from_index(sid,3);assert eca_step(x,90)==tuple(x[(i-1)%3]^x[(i+1)%3] for i in range(3))
@pytest.mark.parametrize("sid",range(8))
def test_rule60(sid):
 x=bits_from_index(sid,3);assert eca_step(x,60)==tuple(x[(i-1)%3]^x[i] for i in range(3))
def test_evolve():
 g=eca_evolve((0,0,1,0,0),30,6);assert g.shape==(7,5) and tuple(g[1])==eca_step(g[0],30)
@pytest.mark.parametrize("rule",[30,60,90])
@pytest.mark.parametrize("xid",range(8))
@pytest.mark.parametrize("yid",range(8))
def test_reversible(rule,xid,yid):
 x=bits_from_index(xid,3);y=bits_from_index(yid,3);ox,oy=oracle_basis_output(x,rule,y);assert ox==x;assert oy==tuple(a^b for a,b in zip(y,eca_step(x,rule)));assert oracle_basis_output(ox,rule,oy)==(x,y)
@pytest.mark.parametrize("rule",[30,60,90])
def test_oracle_involution(rule):
 rng=np.random.default_rng(rule);v=rng.normal(size=64)+1j*rng.normal(size=64);v/=np.linalg.norm(v);one=apply_reversible_oracle(v,rule,3);np.testing.assert_allclose(apply_reversible_oracle(one,rule,3),v,atol=1e-14);assert np.linalg.norm(one)==pytest.approx(1)
@pytest.mark.parametrize("rule",[30,60,90])
@pytest.mark.parametrize("sid",range(8))
def test_basis_reference(rule,sid):
 x=bits_from_index(sid,3);v=oracle_statevector(rule,3,initial=x);assert np.argmax(abs(v)**2)==index_from_bits(x+eca_step(x,rule));assert fidelity(v,v)==pytest.approx(1)
@pytest.mark.parametrize("rule",[30,60,90])
def test_plus_entropy(rule):
 v=oracle_statevector(rule,3,plus_input=True);assert np.linalg.norm(v)==pytest.approx(1);assert 0<=von_neumann_entropy_input(v,3)<=3+1e-12
@pytest.mark.parametrize("rule",[30,60,90])
@pytest.mark.parametrize("sid",range(8))
def test_z(rule,sid):
 x=bits_from_index(sid,3);v=oracle_statevector(rule,3,initial=x);np.testing.assert_allclose(output_z_expectations(v,3),[1-2*b for b in eca_step(x,rule)])
def test_profile_streams():
 s=PROFILE_SPECS["smoke"];keys=list(itertools.product(s.rules,s.noise_state_ids,s.bitflip_probabilities,s.base_seeds));assert len(keys)==len({derive_seed("noise",*k) for k in keys})==36
def test_seed():assert derive_seed("x",1,2)==derive_seed("x",1,2)!=derive_seed("x",2,1)
def test_noise_edges():
 assert sample_output_bitflip((1,0,1),0,100,7)==(0,1);ber,exact=sample_output_bitflip((1,0,1),.5,50000,7);assert ber==pytest.approx(.5,abs=.005);assert exact==pytest.approx(.125,abs=.006)
def test_bootstrap():
 a=bootstrap_percentile_ci([.1,.2,.3,.4],resamples=500,seed=12);assert a==bootstrap_percentile_ci([.1,.2,.3,.4],resamples=500,seed=12);assert a[0]<=.25<=a[1]
@pytest.mark.parametrize("call",[
 lambda:wolfram_local(256,0,0,0),lambda:eca_step((0,1),30),lambda:eca_step((0,1,0),30,boundary="fixed"),lambda:bits_from_index(8,3),lambda:oracle_statevector(30,3),lambda:oracle_statevector(30,3,initial=(0,0,0),plus_input=True),lambda:sample_output_bitflip((0,1,0),.6,10,1),lambda:bootstrap_percentile_ci([],resamples=10,seed=1),lambda:apply_reversible_oracle([1],30,3),lambda:index_from_bits((0,2))])
def test_invalid(call):
 with pytest.raises(ValueError):call()
def test_invalid_spec():
 with pytest.raises(ValueError):ExperimentSpec("bad",3,(0,),(0,),(.1,),(1,),10,10,1)
