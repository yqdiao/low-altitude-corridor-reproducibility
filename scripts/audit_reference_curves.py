"""Compare analytical values to ORIGINAL vector-path vertices, not rendered pixels.

Optional: pip install pymupdf==1.27.2.3
Axes mappings use tick coordinates in the archived standalone PDF figures.
This independently checks five single-panel plots. Other panels are covered by
model optimality tests and manuscript numerical landmarks, not pixel matching.
"""
import sys,json
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import fitz,numpy as np
from corridor.models import *
p=Parameters()
BLUE=(0.,.4470588267,.6980392337);ORANGE=(.9019607902,.6235294342,0.);GREEN=(0.,.6196078658,.4509803951)
# x-coordinate at x0, points per x unit; y-coordinate at y0, points per y unit.
axes={1:(62.8035049438,82.1656188965,0.,191.7402801514,-9.487600708,0.),
      3:(67.1959075928,113.327270508,1.,138.7729187012,-2653.60412598,1.),
      4:(67.6941833496,56.5687255859,0.,191.6177368164,-1058.38909149,.54),
      5:(45.9110527039,43.4586143494,1.,180.9107055664,-59.3475494385,1.5),
      6:(60.2883148193,72.5173797607,.5,188.9807891846,-42.7065582275,.5)}
names={1:'revenue_ranking',3:'objective_ratio',4:'coordination_threshold',5:'capacity_comparison',6:'state_contingent_release'}
records=[]
for number,name in names.items():
 page=fitz.open(ROOT/'reference_figures'/f'fig{number}_{name}.pdf')[0]
 xp,xs,x0,yp,ys,y0=axes[number]
 for curve in page.get_drawings():
  if curve['fill'] is not None or len(curve['items'])<3 or curve['color'] is None:continue
  colors=[BLUE,ORANGE,GREEN];distance=[np.linalg.norm(np.array(curve['color'])-c) for c in colors]
  j=int(np.argmin(distance))
  if distance[j]>1e-5:continue
  points=[]
  for item in curve['items']:
   if item[0]=='l':points.extend([item[1],item[2]])
  if not points:continue
  xy=np.array([(q.x,q.y) for q in points]);x=(xy[:,0]-xp)/xs+x0;y=(xy[:,1]-yp)/ys+y0
  if number==1:
   if j==2: expected=(p.a-p.tbar-(p.g+p.kappa)*x)*x;label='truthful interior curve'
   elif j==0:expected=revenues(x,p)[1];label='VCG piecewise'
   else:expected=auction(x,p)['U'];label='MUPA'
  elif number==3:
   pp=replace(p,Delta=[0.,2.,4.][j]);A=model_a(x,pp);M=auction(auction_supply(x,pp),pp)
   expected=(M['W']+(x-1)*M['U'])/A['OF'];label=f'ratio Delta={pp.Delta:g}'
  elif number==4:
   expected=np.array([coordination(2.5,replace(p,Delta=max(0,float(v))))['threshold'] for v in x]);label='grim-trigger threshold'
  elif number==5:
   expected=capacities(2,x,p)[j];label=['Nash capacity','coordinated capacity'][j]
  else:
   expected=release(x,[20.,12.][j],1.5,p)['N'];label=['high-demand release','low-demand release'][j]
  err=float(np.max(np.abs(y-expected)));records.append(dict(figure=number,curve=label,vertices=len(x),max_absolute_error=err))
  if err>2e-5:raise AssertionError(records[-1])
report={'method':'Original PDF vector-path vertices transformed using original axis tick coordinates; analytical evaluation at those x coordinates. Not a pixel or byte-identity test.','absolute_tolerance':2e-5,'all_passed':True,'curves':records}
(ROOT/'docs'/'reference_curve_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
