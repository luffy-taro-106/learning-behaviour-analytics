"""Secondary checks motivated by data quality and interpretation, not model selection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[1];result=json.loads((ROOT/'results/results.json').read_text());key=['code_module','code_presentation','id_student']
d=pd.read_csv(ROOT/'data/processed/oulad_features.csv');info=pd.read_csv(ROOT/'data/raw/oulad/studentInfo.csv')
seen=set(info.loc[info.code_presentation.str.startswith('2013'),'id_student'])
ctx=set(d.loc[d.year.eq(2013),'context']);mask=d.year.eq(2014)&~d.id_student.isin(seen)&d.context.isin(ctx)
formula=result['oulad']['inference_formula']
def eff(f,k):
 lo,hi=f.conf_int().loc[k];return {'or':float(np.exp(f.params[k])),'lo':float(np.exp(lo)),'hi':float(np.exp(hi)),'p':float(f.pvalues[k])}
def infer(z):
 f=smf.glm(formula,data=z,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':z.id_student});return {'O1':eff(f,'active7'),'O2':eff(f,'momentum')}
out={}
v=pd.read_csv(ROOT/'data/raw/oulad/studentVle.csv',dtype={'code_module':'category','code_presentation':'category','id_student':'int32','id_site':'int32','date':'int16','sum_click':'int32'})
v=v[v.date.between(0,55)];out['early_exact_duplicates_removed']=int(v.duplicated().sum());v=v.drop_duplicates()
for c in ['code_module','code_presentation']:v[c]=v[c].astype(str)
a=v.groupby(key+['date'],observed=True).sum_click.sum().unstack('date').reindex(columns=range(56),fill_value=0).fillna(0).reindex(pd.MultiIndex.from_frame(d[key]),fill_value=0).to_numpy()
dd=d.copy();dd['log_clicks']=np.log1p(a.sum(1));dd['momentum']=np.log1p(a[:,42:56].sum(1))-np.log1p(a[:,28:42].sum(1))
assert ((a>0).sum(1)==dd.active_days).all()
out['deduplicated_associations']=infer(dd[mask]);out['fail_only_associations']=infer(d[mask & d.final_result.ne('Withdrawn')]);out['fail_only_n']=int((mask & d.final_result.ne('Withdrawn')).sum())
# Isolate temporal features from on-time submission information using a fixed model.
cols=['log_clicks','num_of_prev_attempts','credits60','ontime_share','no_due']
abl={}
for name,fields in [('Volume + submissions',cols),('+ active days',cols+['active7']),('+ momentum',cols+['momentum']),('+ both',cols+['active7','momentum'])]:
 h=d[d.year.eq(2013)];tr,va=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=610).split(h,groups=h.id_student))
 model=make_pipeline(ColumnTransformer([('num',StandardScaler(),fields),('cat',OneHotEncoder(handle_unknown='ignore'),['context'])]),LogisticRegression(C=1,max_iter=3000,random_state=610))
 model.fit(h.iloc[tr],h.iloc[tr].risk)
 abl[name]=float(roc_auc_score(d.loc[mask,'risk'],model.predict_proba(d[mask])[:,1]))
out['temporal_ablation_test_auroc']=abl
m=pd.read_csv(ROOT/'data/processed/moodle_features.csv');m['prop']=m.future_days/28
f=smf.glm('prop ~ active7 + log_events + entropy + arrival_week',data=m,family=sm.families.Binomial()).fit(cov_type='HC3')
out['moodle_fractional_logit']={'M1':eff(f,'active7'),'M2':eff(f,'entropy')}
out['moodle_ols_support']='Bounded fractional-logit model used only as directional sensitivity; no independent-day assumption or causal interpretation.'
(ROOT/'results/robustness.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
