#!/usr/bin/env python3
"""One command regenerates all eight figures and their underlying CSV data."""
import argparse,json,os,hashlib,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import scipy
from dataclasses import replace
from corridor.models import Parameters,model_a,auction_supply,auction,revenues,capacities,coordination,release,investment,one_shot_zero

NAMES=['fig1_revenue_ranking','fig2_mechanism_quantities','fig3_objective_ratio',
       'fig4_coordination_threshold','fig5_capacity_comparison','fig6_state_contingent_release',
       'fig7_investment_uncertainty','fig8_regime_maps']
BLUE,ORANGE,GREEN,GRAY='#0072B2','#E69F00','#009E73','#777777'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':10,
 'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,
 'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':300,'lines.linewidth':1.8,
 'axes.prop_cycle':plt.cycler(color=[BLUE,ORANGE,GREEN]),'svg.hashsalt':'corridor-reproducibility'})

def grid(spec): return np.linspace(spec[0],spec[1],int(spec[2]))

def csv(path,**columns):
    vals=np.column_stack([np.asarray(v).ravel() for v in columns.values()])
    np.savetxt(path,vals,delimiter=',',header=','.join(columns),comments='',fmt='%.12g')

def line(ax,x,y,valid,*,color,label,invalid_style=':'):
    ax.plot(x,np.where(valid,y,np.nan),color=color,label=label)
    ax.plot(x,np.where(~valid,y,np.nan),color=color,ls=invalid_style)

def fig1(c,p,d):
    N=grid(c['N']); ns_corner,v,m=revenues(N,p); valid=auction(N,p)['valid']
    # Original Fig. 1 uses the interior truthful formula even below its allocation boundary.
    ns=(p.a-p.tbar-(p.g+p.kappa)*N)*N
    fig,ax=plt.subplots(figsize=(5.2,3.3),layout='constrained')
    ax.plot(N,ns,color=GREEN,label='Non-strategic bids'); ax.plot(N,v,color=BLUE,label='VCG (piecewise)')
    line(ax,N,m,valid,color=ORANGE,label='Affine MUPA')
    for x,ls,label in [(p.Delta/(4*p.kappa),':',r'$\Delta/(4\kappa)$'),(p.Delta/(2*p.kappa),'--',r'$\Delta/(2\kappa)$')]:
        ax.axvline(x,color=GRAY,ls=ls,lw=1); ax.text(x-.025,15.5,label,rotation=90,ha='right',va='top',fontsize=8)
    ax.set(xlabel=r'Auction release $N$',ylabel='Platform revenue'); ax.legend(loc='lower center',bbox_to_anchor=(.6,.02),fontsize=8)
    csv(d/'fig1.csv',N=N,U_NS_original_curve=ns,U_NS_piecewise=ns_corner,U_VCG=v,U_MUPA=m,mupa_valid=valid,efficient_interior=N>p.Delta/(2*p.kappa))
    return fig

def fig2(c,p,d):
    alpha=grid(c['alpha']); A=model_a(alpha,replace(p,Delta=c['A_Delta']))
    pb=replace(p,Delta=c['B_Delta'],tbar=c['B_tbar']); N=auction_supply(alpha,pb); valid=auction(N,pb)['valid']
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.1),layout='constrained')
    for key,label,color in [('Q',r'$Q_A^*$',BLUE),('q1',r'$q_{1A}^*$',ORANGE),('q2',r'$q_{2A}^*$',GREEN)]:
        line(axs[0],alpha,A[key],A['interior'],color=color,label=label,invalid_style='--')
    axs[0].set(title=fr'(a) Model A ($\Delta={c["A_Delta"]:g}$)',xlabel=r'Revenue weight $\alpha$',ylabel='Traffic volume'); axs[0].legend(fontsize=8)
    line(axs[1],alpha,N,valid,color=BLUE,label=r'$N_M^*$ (interior)')
    axs[1].plot([],[],':',color=BLUE,label='Outside interior')
    axs[1].axhline(pb.Delta/(4*pb.kappa),ls='--',color=GRAY,label=r'$\Delta/(4\kappa)$')
    axs[1].set(title=fr'(b) Model B ($\Delta={c["B_Delta"]:g}$)',xlabel=r'Revenue weight $\alpha$',ylabel='Auction release'); axs[1].legend(fontsize=8)
    csv(d/'fig2.csv',alpha=alpha,Q_A=A['Q'],q1_A=A['q1'],q2_A=A['q2'],A_interior=A['interior'],N_M=N,M_valid=valid)
    return fig

def fig3(c,p,d):
    alpha=grid(c['alpha']); fig,ax=plt.subplots(figsize=(5.2,3.3),layout='constrained')
    cols={'alpha':alpha}
    for delta,style in zip(c['Deltas'],['-','--','-.']):
        pp=replace(p,Delta=delta); A=model_a(alpha,pp); N=auction_supply(alpha,pp); M=auction(N,pp)
        if not np.all(A['interior']&M['valid']): raise ValueError('Fig. 3 left the common interior.')
        ratio=(M['W']+(alpha-1)*M['U'])/A['OF']
        ax.plot(alpha,ratio,ls=style,label=fr'$\Delta={delta:g}$'); cols[f'ratio_Delta_{delta:g}']=ratio
    ax.axhline(1,color=GRAY,lw=.8,ls=':'); ax.set(xlabel=r'Revenue weight $\alpha$',ylabel=r'Objective ratio $OF_M/OF_A$')
    ax.legend(title='Cost asymmetry',fontsize=8); csv(d/'fig3.csv',**cols)
    return fig

def fig4(c,p,d):
    delta=grid(c['Delta']); results=[coordination(c['K'],replace(p,Delta=x)) for x in delta]
    if not all(r['valid'] for r in results): raise ValueError('Fig. 4 invalid full-capture deviation.')
    thresholds=np.array([r['by_operator'] for r in results]); top=thresholds.max(axis=1)
    fig,ax=plt.subplots(figsize=(5.2,3.3),layout='constrained')
    ax.plot(delta,top,label=r'Flat zero-bid path: $\delta^*(K)$ (operator 1 binds)')
    ax.set(xlabel=r'Cost asymmetry $\Delta$',ylabel=r'Coordination threshold $\delta^*(K)$'); ax.legend(fontsize=7,loc='upper left')
    csv(d/'fig4.csv',Delta=delta,delta1=thresholds[:,0],delta2=thresholds[:,1],delta_star=top)
    return fig

def fig5(c,p,d):
    R=grid(c['R']); N,C=capacities(c['alpha'],R,p); delta=1-R/p.r; test=coordination(C,p)
    if not np.all(test['valid']&(delta>=test['threshold'])): raise ValueError('Fig. 5 coordination infeasible.')
    if not np.all((N>p.Delta/(4*p.kappa))&(p.m-(p.b+2*p.kappa)*N>0)): raise ValueError('Fig. 5 Nash invalid.')
    fig,ax=plt.subplots(figsize=(5.2,3.3),layout='constrained')
    ax.fill_between(R,N,C,where=C>=N,color=ORANGE,alpha=.09)
    ax.fill_between(R,N,C,where=N>=C,color=BLUE,alpha=.09)
    ax.plot(R,N,label=r'Nash path $K_N^*$ (conditional reserve candidate)')
    ax.plot(R,C,ls='--',label=r'Coordinated path, no reserve $K_C^*$')
    ax.axvline(p.b+3*p.kappa,color=GRAY,ls=':',label=r'$R=b+3\kappa$')
    ax.set(xlabel=r'Discounted investment parameter $R=r(1-\delta)$',ylabel='Capacity'); ax.legend(fontsize=7)
    csv(d/'fig5.csv',R=R,delta=delta,K_N=N,K_C=C,delta_star=test['threshold'],sustainable=delta>=test['threshold'])
    return fig

def fig6(c,p,d):
    K=grid(c['K']); fig,ax=plt.subplots(figsize=(5.2,3.3),layout='constrained'); cols={'K':K}
    for a,style,name in zip(c['states'],['-','--'],['Low','High']):
        s=release(K,a,c['alpha'],p)
        if not s['valid'].all(): raise ValueError('Fig. 6 release outside affine branch.')
        ax.plot(K,s['N'],ls=style,color=ORANGE if name=='Low' else BLUE,label=fr'{name} demand $a={a:g}$')
        cols[f'N_{name}']=s['N'];cols[f'y_{name}']=s['y'];cols[f'valid_{name}']=s['valid']
    ax.plot(K,K,color=GRAY,ls=':',label=r'Full release $N=K$')
    ax.set(xlabel=r'Installed capacity $K$',ylabel=r'Optimal release $N_\omega^*(K)$');ax.legend(fontsize=8)
    csv(d/'fig6.csv',**cols); return fig

def fig7(c,p,d):
    spread=grid(c['spread']); phi=grid(c['probability_high'])
    sr=[investment([c['mean']-s,c['mean']+s],[.5,.5],c['alpha'],p) for s in spread]
    pr=[investment(c['states'],[1-x,x],c['alpha'],p) for x in phi]
    K=np.array([s['K'] for s in sr]); relief=np.array([s['relief'] for s in sr]); scarcity=np.array([s['scarcity'] for s in sr])
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.1),layout='constrained'); ax=axs[0]; twin=ax.twinx()
    ax.plot(spread,K,color=BLUE,label=r'$K^*$');twin.plot(spread,relief,color=ORANGE,ls='--',label='Congestion relief');twin.plot(spread,scarcity,color=GREEN,ls='-.',label='Scarcity rent')
    ax.set(title='(a) Mean-preserving spread',xlabel=r'Demand spread $s$ ($a_{L,H}=16\mp s$)',ylabel=r'Optimal installed capacity $K^*$')
    twin.set(ylabel=r'Marginal benefit terms, sum $=RK^*$',ylim=(0,7.5));twin.spines['right'].set_visible(True)
    handles,labels=ax.get_legend_handles_labels(); h,l=twin.get_legend_handles_labels();ax.legend(handles+h,labels+l,fontsize=6.5,loc='upper left')
    axs[1].plot(phi,[r['K'] for r in pr],color=BLUE);axs[1].set(title='(b) State probability',xlabel=r'High-state probability $\varphi_H$',ylabel=r'Optimal installed capacity $K^*$')
    csv(d/'fig7a.csv',spread=spread,a_low=c['mean']-spread,a_high=c['mean']+spread,K=K,congestion_relief=relief,scarcity_rent=scarcity,RK=p.R*K,N_low=[s['states']['N'][0] for s in sr],N_high=[s['states']['N'][1] for s in sr],residual=[s['residual'] for s in sr])
    csv(d/'fig7b.csv',probability_high=phi,K=[r['K'] for r in pr],N_low=[r['states']['N'][0] for r in pr],N_high=[r['states']['N'][1] for r in pr],residual=[r['residual'] for r in pr])
    return fig

def fig8(c,p,d):
    x=grid(c['B_over_b']); y=grid(c['kappa_over_b']); X,Y=np.meshgrid(x,y)
    delta=grid(c['Delta']); K=grid(c['K']); DD,KK=np.meshgrid(delta,K); s=one_shot_zero(KK,DD,p)
    region=np.where(~s['nash'],0,np.where(s['test'],2,1))
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.3),layout='constrained'); ax=axs[0]
    ax.fill_between(x,0,(1+x)/2,color=ORANGE,alpha=.12);ax.fill_between(x,1+x,y[-1],where=1+x<y[-1],color=BLUE,alpha=.10)
    ax.plot(x,(1+x)/2,color=ORANGE);ax.plot(x,1+x,color=BLUE);ax.axvline(1,color=GRAY,ls='--',lw=1)
    ax.scatter([p.B/p.b],[p.kappa/p.b],color='black',s=18);ax.annotate('baseline',(p.B/p.b,p.kappa/p.b),xytext=(5,6),textcoords='offset points',fontsize=7)
    ax.text(.12,2.58,'Free access\nunderuses',fontsize=7);ax.text(1.85,2.58,'Free access\noveruses',fontsize=7)
    ax.text(.1,1.72,r'$b+B<\kappa$:'+' VCG raises\nless than FB fees',fontsize=7,bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=1))
    ax.text(1.2,.16,r'$b+B>2\kappa$:'+' MUPA beats\nbest uniform charge',fontsize=6.7)
    ax.set(xlim=(x[0],x[-1]),ylim=(y[0],y[-1]),title='(a) Static comparisons (Models A-B)',xlabel=r'Congestion-to-demand slope ratio $B/b$',ylabel=r'Operating-cost curvature $\kappa/b$')
    ax=axs[1];ax.pcolormesh(DD,KK,region,cmap=ListedColormap(['#e0e0e0','#f4d8b3','#c5e4dd']),shading='auto',rasterized=True,vmin=0,vmax=2)
    for disc,ls in zip(c['discounts'],['--','-.']):
        kc=p.m/(p.b+p.kappa+p.r*(1-disc));ax.axhline(kc,color=BLUE,ls=ls,lw=1);ax.text(.2,kc+.05,fr'$K_C^*,\ \delta={disc:g}$',fontsize=7)
    ax.axhline(2.5,color=GRAY,ls=':',lw=1);ax.text(.2,2.55,'Fig. 4 slice',fontsize=7)
    ax.text(1.9,1.45,'Zero-price split is\na one-shot equilibrium',fontsize=7);ax.text(7,3.55,'One-shot test\nnot satisfied',fontsize=7);ax.text(6.5,.82,'No two-operator\nNash branch',fontsize=7)
    ax.set(title='(b) Coordination in Model C',xlabel=r'Cost asymmetry $\Delta$',ylabel=r'Installed capacity $K$',xlim=(delta[0],delta[-1]),ylim=(K[0],K[-1]))
    # Full original Delta range is retained; invalid primitive costs are flagged in data/docs.
    csv(d/'fig8a.csv',B_over_b=X,kappa_over_b=Y,free_access_overuse=X>1,mupa_beats_uniform=(1+X)>2*Y,vcg_exceeds_fees=(1+X)>Y)
    csv(d/'fig8b.csv',Delta=DD,K=KK,region=region,nash_valid=s['nash'],one_shot_test=s['test'],primitive_cost_valid=s['primitive_cost_valid'])
    return fig

FUNCTIONS=[fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,default=ROOT/'config/parameters.json');parser.add_argument('--output',type=Path,default=ROOT);parser.add_argument('--figure',type=int,choices=range(1,9));args=parser.parse_args()
    c=json.loads(args.config.read_text());p=Parameters(**c['baseline']);p.validate()
    out=args.output.resolve();d=out/'data';f=out/'figures';d.mkdir(parents=True,exist_ok=True);f.mkdir(parents=True,exist_ok=True)
    selected=[args.figure] if args.figure else list(range(1,9));files=[]
    for i in selected:
        fig=FUNCTIONS[i-1](c[f'fig{i}'],p,d)
        for ext in ['pdf','png']:
            path=f/f'{NAMES[i-1]}.{ext}';kw={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}
            fig.savefig(path,**kw);files.append(path)
        plt.close(fig);print('Generated',NAMES[i-1])
    files+=sorted(d.glob('fig*.csv'))
    report=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),figures=selected,files={str(x.relative_to(out)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files})
    (out/'reproduction_manifest.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
