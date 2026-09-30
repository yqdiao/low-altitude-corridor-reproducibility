"""Equations are identified by the manuscript's stable LaTeX labels.

Static formulas use C(N)=B*N. Dynamic formulas use
C(N,K)=B*N/K + gamma/2*(N/K)**2. Never mix these normalizations.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import brentq

@dataclass(frozen=True)
class Parameters:
    a: float = 20.
    b: float = 1.
    tbar: float = 4.
    kappa: float = 1.
    Delta: float = 2.
    B: float = 1.5
    gamma: float = 1.
    r: float = 30.
    delta: float = .9

    @property
    def t1(self): return self.tbar - self.Delta / 2
    @property
    def t2(self): return self.tbar + self.Delta / 2
    @property
    def g(self): return self.b + self.B
    @property
    def m(self): return self.a - self.tbar - self.B - self.gamma / 2
    @property
    def R(self): return self.r * (1 - self.delta)

    def validate(self):
        if not (self.a > 0 and self.b > 0 and self.kappa > 0 and
                self.t1 > 0 and self.Delta >= 0 and self.B >= 0 and
                self.gamma >= 0 and self.r > 0 and 0 < self.delta < 1):
            raise ValueError('Parameters violate maintained primitive conditions.')


def dn(alpha, p):
    return p.b + p.kappa + 2 * (alpha - 1) * (p.b + 2 * p.kappa)


def model_a(alpha, p):
    """eq:model-a-total through eq:model-a-corner, including active-set choice."""
    alpha = np.asarray(alpha)
    L = p.b + 2*p.B + 2*(alpha-1)*p.g
    M = p.kappa + (alpha-1)*(p.g+2*p.kappa)
    Q = alpha*(p.a-p.tbar)/(L+M)
    q1, q2 = Q/2+alpha*p.Delta/(4*M), Q/2-alpha*p.Delta/(4*M)
    interior = q2 > 0
    corner_q = np.maximum(0, alpha*(p.a-p.t1)/(L+2*M))
    q1, q2 = np.where(interior,q1,corner_q), np.where(interior,q2,0.)
    Q = q1+q2
    z1 = p.a-p.g*Q-p.t1-(p.g+2*p.kappa)*q1
    z2 = p.a-p.g*Q-p.t2-(p.g+2*p.kappa)*q2
    U = z1*q1+z2*q2
    W = p.a*Q-(p.b/2+p.B)*Q**2-p.t1*q1-p.t2*q2-p.kappa*(q1*q1+q2*q2)
    return dict(Q=Q,q1=q1,q2=q2,z1=z1,z2=z2,U=U,W=W,OF=W+(alpha-1)*U,interior=interior)


def auction_supply(alpha, p):
    return alpha*(p.a-p.tbar)/(p.b+2*p.B+p.kappa+2*(alpha-1)*(p.g+2*p.kappa))


def auction(N, p):
    """Interior MUPA formulas. Caller must use the returned validity mask."""
    N=np.asarray(N)
    q1,q2=N/2+p.Delta/(8*p.kappa),N/2-p.Delta/(8*p.kappa)
    y=p.a-p.tbar-(p.g+2*p.kappa)*N
    W=(p.a-p.tbar)*N-(p.b+2*p.B+p.kappa)*N**2/2+3*p.Delta**2/(32*p.kappa)
    return dict(q1=q1,q2=q2,y=y,U=N*y,W=W,valid=(q2>0)&(y>0))


def revenues(N, p):
    """Truthful and VCG allocation corners are evaluated explicitly."""
    N=np.asarray(N)
    A1,A2=p.a-p.g*N-p.t1,p.a-p.g*N-p.t2
    efficient_interior=N>p.Delta/(2*p.kappa)
    U_NS=np.where(efficient_interior,(p.a-p.tbar-(p.g+p.kappa)*N)*N,
                  (A1-2*p.kappa*N)*N)
    U_V=np.where(efficient_interior,(p.a-p.tbar-(p.g+1.5*p.kappa)*N)*N-p.Delta**2/(8*p.kappa),
                 A2*N-p.kappa*N*N)
    return U_NS,U_V,auction(N,p)['U']


def capacities(alpha, R, p):
    R=np.asarray(R)
    return alpha*p.m/(dn(alpha,p)+R),p.m/(p.b+p.kappa+R)


def coordination(K, p):
    """Flat-zero bids with full-capture deviation; eq:delta-threshold."""
    K=np.asarray(K)
    A=np.stack([p.a-p.b*K-p.B-p.gamma/2-p.t1,
                p.a-p.b*K-p.B-p.gamma/2-p.t2],axis=-1)
    q=np.stack([K/2+p.Delta/(8*p.kappa),K/2-p.Delta/(8*p.kappa)],axis=-1)
    C=A*K[...,None]/2-p.kappa*K[...,None]**2/4
    D=A*K[...,None]-p.kappa*K[...,None]**2
    Nash=3*p.kappa*q**2
    with np.errstate(divide='ignore',invalid='ignore'):
        threshold=np.where(D<=C,0.,np.where(D>Nash,(D-C)/(D-Nash),np.inf))
    valid=(K>p.Delta/(4*p.kappa))&(p.m-(p.b+2*p.kappa)*K>0)&(A[...,1]>=2*p.kappa*K)
    return dict(threshold=threshold.max(axis=-1),by_operator=threshold,valid=valid,C=C,D=D,Nash=Nash)


def one_shot_zero(K, Delta, p):
    """Proposition 6 test, including exact constrained deviation maximum.

    Allows Delta grids beyond 2*tbar solely to match the original Fig. 8;
    primitive_cost_valid separately flags that algebraic extrapolation.
    """
    K,Delta=np.broadcast_arrays(K,Delta)
    Abar=p.m-p.b*K
    A1,A2=Abar+Delta/2,Abar-Delta/2
    qdev=np.clip((Delta+2*p.kappa*K)/(6*p.kappa),K/2,K)
    deviation=(Delta+2*p.kappa*K)*qdev-3*p.kappa*qdev*qdev
    equal_payoff=A1*K/2-p.kappa*K*K/4
    condition=(A2>=p.kappa*K)&((Delta<=p.kappa*K)|(deviation<=equal_payoff+1e-12))
    nash=(K>Delta/(4*p.kappa))&(p.m-(p.b+2*p.kappa)*K>0)
    return dict(test=condition,nash=nash,primitive_cost_valid=Delta<2*p.tbar)


def release(K, a, alpha, p):
    """eq:unconstrained-utilization, using the stable rationalized root."""
    K,a=np.broadcast_arrays(np.asarray(K,dtype=float),np.asarray(a,dtype=float))
    if np.any(K<=0) or np.any(a<=p.tbar) or alpha<1:
        raise ValueError('Release candidate requires K>0, a>tbar, alpha>=1.')
    H=dn(alpha,p)*K+2*alpha*p.B
    xhat=2*alpha*(a-p.tbar)/(H+np.sqrt(H*H+6*alpha*alpha*p.gamma*(a-p.tbar)))
    x=np.minimum(1.,xhat)
    N=K*x
    C=p.B*x+p.gamma*x*x/2
    y=a-p.tbar-(p.b+2*p.kappa)*N-C
    mu=np.maximum(0.,alpha*(a-p.tbar)-dn(alpha,p)*K-2*alpha*p.B-1.5*alpha*p.gamma)
    relief=alpha*(p.B*x*x+p.gamma*x**3)
    F=alpha*(a-p.tbar)*N-dn(alpha,p)*N*N/2-alpha*C*N+3*p.Delta**2/(32*p.kappa)
    return dict(N=N,x=x,y=y,mu=mu,relief=relief,F=F,valid=(N>p.Delta/(4*p.kappa))&(y>0))


def investment(states, probs, alpha, p):
    """Solve envelope FOC, then check ALL statewise auction domains."""
    states,probs=np.asarray(states,dtype=float),np.asarray(probs,dtype=float)
    if states.shape!=probs.shape or np.any(probs<0) or not np.isclose(probs.sum(),1):
        raise ValueError('State probabilities must be non-negative and sum to 1.')
    def residual(K):
        s=release(K,states,alpha,p)
        return p.R*K-np.dot(probs,s['relief']+s['mu'])
    upper=max(1.,alpha*(states.max()-p.tbar)/p.R)
    while residual(upper)<0: upper*=2
    K=brentq(residual,1e-10,upper,xtol=1e-12)
    s=release(K,states,alpha,p)
    if not np.all(s['valid']):
        raise ValueError('Investment candidate crosses the maintained auction domain.')
    return dict(K=K,relief=float(np.dot(probs,s['relief'])),scarcity=float(np.dot(probs,s['mu'])),
                residual=residual(K),states=s)
