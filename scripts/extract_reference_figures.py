"""Extract the eight original vector Form XObjects from a compiled paper PDF.

Optional archival utility: pip install pypdf==6.9.2
Usage: python scripts/extract_reference_figures.py /path/to/paper.pdf
No Overleaf cookies, edit tokens, or credentials are needed or stored.
"""
import sys,json,hashlib
from pathlib import Path
from pypdf import PdfReader,PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
ROOT=Path(__file__).resolve().parents[1]
NAMES=['fig1_revenue_ranking','fig2_mechanism_quantities','fig3_objective_ratio',
       'fig4_coordination_threshold','fig5_capacity_comparison','fig6_state_contingent_release',
       'fig7_investment_uncertainty','fig8_regime_maps']
source=Path(sys.argv[1]); reader=PdfReader(source); records=[]
for page_no,page in enumerate(reader.pages,1):
    objects=page.get('/Resources',{}).get('/XObject',{})
    if hasattr(objects,'get_object'): objects=objects.get_object()
    for key,ref in objects.items():
        if str(key) not in [f'/Im{i}' for i in range(1,9)]: continue
        i=int(str(key)[3:])-1
        obj=ref.get_object()
        if obj.get('/Subtype')!='/Form': continue
        bbox=list(map(float,obj['/BBox'])); writer=PdfWriter()
        output=writer.add_blank_page(width=bbox[2]-bbox[0],height=bbox[3]-bbox[1])
        copied=obj.clone(writer)
        output[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Figure'):copied.indirect_reference})})
        stream=DecodedStreamObject(); stream.set_data(f'q 1 0 0 1 {-bbox[0]} {-bbox[1]} cm /Figure Do Q'.encode())
        output[NameObject('/Contents')]=writer._add_object(stream)
        dest=ROOT/'reference_figures'/f'{NAMES[i]}.pdf'
        dest.parent.mkdir(exist_ok=True); writer.write(dest)
        records.append(dict(figure=i+1,page=page_no,file=dest.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
if len(records)!=8: raise RuntimeError(f'Expected 8 figures, found {len(records)}')
(ROOT/'reference_figures'/'manifest.json').write_text(json.dumps(dict(
    provenance='Vector Form XObjects extracted from the user-provided Overleaf project compiled PDF; not original standalone PDF byte streams.',
    captured_date='2026-09-30',source_pdf_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),figures=records),indent=2)+'\n')
print('Extracted',len(records),'original vector figures.')
