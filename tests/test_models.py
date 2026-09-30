"""Independent optimality, accounting, boundary, and manuscript landmark checks."""
import unittest
from dataclasses import replace
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from corridor.models import *

class ReproductionTests(unittest.TestCase):
    def setUp(self): self.p=Parameters()

    def test_manuscript_welfare_table(self):
        expected=[(1,3.2,26.100,1.310,25.975,5.120),
                  (1.5,2.462,24.592,10.586,24.840,11.701),
                  (2,2.207,23.432,12.242,23.885,13.061),
                  (3,2.000,22.255,13.098,22.878,13.792)]
        for alpha,Q,W,U,WM,UM in expected:
            A=model_a(alpha,self.p);M=auction(auction_supply(alpha,self.p),self.p)
            for actual,target in [(A['Q'],Q),(A['W'],W),(A['U'],U),(M['W'],WM),(M['U'],UM)]:
                self.assertLess(abs(actual-target),.00051)

    def test_pricing_against_constrained_optimizer(self):
        for gap in [0,2,7.5]:
            p=replace(self.p,Delta=gap)
            for alpha in [1,1.15,2,4]:
                def objective(q):
                    Q=sum(q);t=np.array([p.t1,p.t2])
                    W=p.a*Q-(p.b/2+p.B)*Q*Q-np.dot(t,q)-p.kappa*np.dot(q,q)
                    z=p.a-p.g*Q-t-(p.g+2*p.kappa)*np.asarray(q)
                    return -(W+(alpha-1)*np.dot(z,q))
                opt=minimize(objective,[1,1],bounds=[(0,None)]*2,tol=1e-11)
                result=model_a(alpha,p)
                np.testing.assert_allclose([result['q1'],result['q2']],opt.x,atol=2e-6)

    def test_auction_best_response_and_accounting(self):
        p=self.p
        for N in [.75,1.5,3.2]:
            m=auction(N,p)
            for i in [0,1]:
                t=[p.t1,p.t2];q=[m['q1'],m['q2']];j=1-i
                Ai=p.a-p.g*N-t[i];Aj=p.a-p.g*N-t[j];sj=2*p.kappa*q[j]
                # Rival affine schedule induces residual price; optimize unrestricted quantity envelope.
                f=lambda x: -(Ai*x-p.kappa*x*x-max(Aj-2*p.kappa*(N-x)-sj,0)*x)
                opt=minimize_scalar(f,bounds=(0,N),method='bounded',options={'xatol':1e-12})
                self.assertAlmostEqual(opt.x,q[i],places=6)
            profits=3*p.kappa*(m['q1']**2+m['q2']**2)
            self.assertAlmostEqual(p.b*N*N/2+profits+m['U'],m['W'],places=10)

    def test_vcg_definition_and_boundary(self):
        p=self.p
        for N in [.2,.75,1,2,3.2]:
            q1=min(N,N/2+p.Delta/(4*p.kappa));q2=N-q1
            V=lambda q,t:(p.a-p.g*N-t)*q-p.kappa*q*q
            payment=V(N,p.t2)-V(q2,p.t2)+V(N,p.t1)-V(q1,p.t1)
            self.assertAlmostEqual(revenues(N,p)[1],payment,places=10)
        self.assertAlmostEqual(revenues(1,p)[1],revenues(1,p)[2])

    def test_coordination_landmarks(self):
        for gap,target in [(0,.54),(5,.70)]:
            s=coordination(2.5,replace(self.p,Delta=gap))
            self.assertTrue(s['valid']);self.assertLess(abs(s['threshold']-target),.005)
            self.assertGreaterEqual(s['by_operator'][0],s['by_operator'][1])
        self.assertTrue(one_shot_zero(2.5,np.linspace(0,5,101),self.p)['test'].all())

    def test_capacity_crossing(self):
        for R in [1.3,4,8]:
            N,C=capacities(2,R,self.p)
            self.assertEqual(np.sign(N-C),np.sign(R-4))
            s=coordination(C,self.p)
            self.assertTrue(s['valid']);self.assertGreaterEqual(1-R/self.p.r,s['threshold'])

    def test_release_optimality_and_gamma_zero(self):
        for gamma in [0,1,2]:
            p=replace(self.p,gamma=gamma)
            for K in [.6,1.5,3,4.5]:
                for a in [12,20]:
                    r=release(K,a,1.5,p);N=float(r['N']);alpha=1.5
                    # Direct polynomial objective independently optimized over 0 <= N <= K.
                    f=lambda n: -(alpha*(a-p.tbar)*n-dn(alpha,p)*n*n/2-alpha*p.B*n*n/K-alpha*p.gamma*n**3/(2*K*K))
                    opt=minimize_scalar(f,bounds=(0,K),method='bounded',options={'xatol':1e-11})
                    self.assertLess(abs(N-opt.x),2e-6)
                    derivative=alpha*(a-p.tbar)-dn(alpha,p)*N-2*alpha*p.B*N/K-1.5*alpha*p.gamma*N*N/K**2
                    self.assertAlmostEqual(derivative,float(r['mu']),places=8)

    def test_stochastic_landmarks_and_foc(self):
        for s in [0,1,1.25,2,6]:
            r=investment([16-s,16+s],[.5,.5],1.5,self.p)
            self.assertLess(abs(r['residual']),1e-9)
            self.assertAlmostEqual(self.p.R*r['K'],r['relief']+r['scarcity'],places=8)
            if s<=1.25:self.assertAlmostEqual(r['K'],1.875,places=9)
            if s==6:self.assertLess(abs(r['K']-2.26),.005)
        for prob,target in [(0,1.15),(1,2.625)]:
            r=investment([12,20],[1-prob,prob],1.5,self.p)
            self.assertLess(abs(r['K']-target),.005)

    def test_stochastic_joint_optimization(self):
        p=self.p;alpha=1.5;states=np.array([10,22]);weights=np.array([.5,.5])
        solution=investment(states,weights,alpha,p)
        def objective(v):
            K=v[0];N=v[1:]
            F=alpha*(states-p.tbar)*N-dn(alpha,p)*N*N/2-alpha*p.B*N*N/K-alpha*p.gamma*N**3/(2*K*K)
            return -(np.dot(weights,F)-p.R*K*K/2)
        opt=minimize(objective,[2,1,2],method='SLSQP',bounds=[(.01,None),(0,None),(0,None)],constraints=[{'type':'ineq','fun':lambda v:v[0]-v[1:]}],options={'ftol':1e-11,'maxiter':1000})
        self.assertTrue(opt.success)
        np.testing.assert_allclose(opt.x,np.r_[solution['K'],solution['states']['N']],atol=2e-6)

    def test_one_shot_deviation_against_dense_grid(self):
        p=self.p
        for K in [1,2.5,4]:
            for D in [0,2,5,7.9]:
                A1=p.m-p.b*K+D/2;A2=p.m-p.b*K-D/2
                q=np.linspace(K/2,K,10001)
                maxdev=np.max((D+2*p.kappa*K)*q-3*p.kappa*q*q)
                expected=(A2>=p.kappa*K) and ((D<=p.kappa*K) or (maxdev<=A1*K/2-p.kappa*K*K/4+1e-10))
                self.assertEqual(bool(one_shot_zero(K,D,p)['test']),expected)
        self.assertFalse(one_shot_zero(2,9,p)['primitive_cost_valid'])

if __name__=='__main__':unittest.main()
