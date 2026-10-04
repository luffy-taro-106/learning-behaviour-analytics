"""Independent checks of cohort accounting, saved predictions, public outputs and PDF."""
from pathlib import Path
import json, hashlib, re
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,confusion_matrix
from sklearn.model_selection import GroupShuffleSplit
from statsmodels.stats.multitest import multipletests
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/results.json').read_text());o=r['oulad'];m=r['moodle'];checks=[]
def check(condition,label):
 assert condition,label
 checks.append(label)
a=o['audit'];check(a['enrolments_raw']-a['removed_registration']-a['removed_withdrawn_before_landmark']==a['landmark_n'],'OULAD cohort accounting')
check(sum(a['landmark_outcomes'].values())==a['landmark_n'],'OULAD outcome accounting')
check(sum(z['n'] for z in o['splits'].values())+a['test_removed_seen_people']+a['test_removed_unseen_context']==a['landmark_n'],'OULAD split exclusion accounting')
ma=m['audit'];check(ma['raw_events']-ma['duplicates']-ma['telemetry_removed']==ma['filtered_all_events'],'Moodle event accounting')
check(ma['raw_users']-ma['late_arrival_excluded']==ma['cohort_n'],'Moodle user accounting')
check(sum(p['n'] for p in m['profiles'])==ma['cohort_n'],'Moodle cluster sizes')
check(m['selected_k']==max(m['k_selection'],key=lambda x:x['silhouette'])['k'],'Cluster k chosen by silhouette')
check(o['selected_by_validation_ap']==max(o['validation'],key=lambda n:o['validation'][n]['ap']),'Classifier selected using validation AP')
h=[o['hypotheses']['O1'],o['hypotheses']['O2'],m['hypotheses']['M1'],m['hypotheses']['M2']]
check(np.allclose(multipletests([z['p'] for z in h],method='holm')[1],[z['p_holm'] for z in h]),'Holm correction independently recomputed')
for name,z in o['models'].items():
 tn,fp,fn,tp=np.array(z['confusion']).ravel();check(tn+fp+fn+tp==o['splits']['test']['n'],f'{name}: confusion count')
 check(np.isclose(z['recall'],tp/(tp+fn)),f'{name}: recall recomputed')
 check(np.isclose(z['precision'],tp/(tp+fp) if tp+fp else 0),f'{name}: precision recomputed')
 check(np.isclose(z['balanced_accuracy'],.5*(tp/(tp+fn)+tn/(tn+fp))),f'{name}: balanced accuracy recomputed')
 check(np.isclose(z['f1'],2*tp/(2*tp+fp+fn)),f'{name}: F1 recomputed')
# When authorized local inputs are present, independently check temporal split and data integrity.
local=ROOT/'data/processed'
if (local/'oulad_features.csv').exists():
 d=pd.read_csv(local/'oulad_features.csv');raw=pd.read_csv(ROOT/'data/raw/oulad/studentInfo.csv')
 seen=set(raw.loc[raw.code_presentation.str.startswith('2013'),'id_student']);hist=d[d.year.eq(2013)]
 tr,va=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=610).split(hist,groups=hist.id_student))
 check(not set(hist.iloc[tr].id_student)&set(hist.iloc[va].id_student),'Person-disjoint training/validation')
 test=d[d.year.eq(2014)&~d.id_student.isin(seen)&d.context.isin(hist.context)]
 check(len(test)==o['splits']['test']['n'] and not set(test.id_student)&seen,'Future test cohort reproduced')
 check(d.active_days.between(0,56).all() and d.ontime_share.between(0,1).all(),'Feature range constraints')
 pred=pd.read_csv(local/'oulad_test_predictions.csv')
 check(np.array_equal(pred.risk,test.risk),'Saved predictions align with independently rebuilt test cohort')
 for name,z in o['models'].items():
  if name not in pred:continue
  for key,metric in [('auroc',roc_auc_score),('ap',average_precision_score),('brier',brier_score_loss)]:
   check(np.isclose(z[key],metric(pred.risk,pred[name])),f'{name}: {key} independently recomputed')
  check(np.array_equal(confusion_matrix(pred.risk,pred[name]>=z['threshold']),z['confusion']),f'{name}: full confusion independently recomputed')
 mf=pd.read_csv(local/'moodle_features.csv');check(mf.future_days.between(0,28).all(),'Moodle follow-up range')
manifest=json.loads((ROOT/'DATA_SHA256.json').read_text())
check(manifest==json.loads((ROOT/'results/input_sha256.json').read_text()),'Results match delivered input manifest')
for name,expected in manifest.items():
 p=ROOT/name
 if p.exists():
  hasher=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):hasher.update(chunk)
  check(hasher.hexdigest()==expected,f'Input SHA-256: {p.name}')
report=ROOT/'output/pdf/Learning_Behaviour_Analytics_Report.pdf';pdf=PdfReader(report)
check(len(pdf.pages)==10,'PDF exactly ten pages')
texts=[p.extract_text() for p in pdf.pages];text='\n'.join(texts)
for name in ['Darshan Sonawane','23b1541','Aditya Singh','23b1524','Ashok Kumar','23b0628']:
 check(name in texts[0],f'Title page includes {name}')
check('Individual contributions' in texts[1], 'Separate contributions page is page 2')
for value in ['Project title', 'Darshan Sonawane', '23b1541', 'Aditya Singh', '23b1524', 'Ashok Kumar', '23b0628', 'Part 1', 'Part 2', 'Part 3']:
 check(value in texts[1], f'Contributions page includes {value}')
check(texts[1].count('1/3 (equal share)')==3, 'All three members have equal one-third shares')
check(all(len(t)>500 for t in texts),'No empty/near-empty PDF page')
check(not re.search(r'\b(TODO|TBD|PLACEHOLDER|NaN)\b',text),'No placeholders in PDF')
check('github.com/luffy-taro-106/learning-behaviour-analytics' in text,'Repository link in PDF')
uris=[]
for page in pdf.pages:
 for a in page.get('/Annots',[]):
  action=a.get_object().get('/A',{})
  if '/URI' in action:uris.append(action['/URI'])
check('https://github.com/luffy-taro-106/learning-behaviour-analytics' in uris,'Clickable repository annotation')
for name in ['oulad_trajectories','oulad_model_curves','moodle_trajectories','moodle_profiles','hypothesis_effects']:
 check((ROOT/'figures'/f'{name}.png').stat().st_size>10000,f'Figure exists: {name}')
summary={'passed':len(checks),'checks':checks,'pdf_pages':len(pdf.pages),'pdf_bytes':report.stat().st_size}
(ROOT/'results/verification.json').write_text(json.dumps(summary,indent=2));print(f'{len(checks)} checks passed. PDF: 10 pages.')
