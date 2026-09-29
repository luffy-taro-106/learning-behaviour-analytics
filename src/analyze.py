"""Reproduce both dataset analyses. Raw data and person-level outputs stay local."""
from pathlib import Path
import json, hashlib, warnings
import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss,
    balanced_accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    silhouette_score, adjusted_rand_score, roc_curve, precision_recall_curve)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'; F=ROOT/'figures'; PRIVATE=ROOT/'data/processed'
for p in [R,F,PRIVATE]:p.mkdir(parents=True,exist_ok=True)
SEED=610
rng=np.random.default_rng(SEED)
np.random.seed(SEED)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','savefig.dpi':190})
COL=['#176B87','#D55E00','#6A51A3','#239B72','#C89117']
sns.set_palette(COL)
res={'seed':SEED,'analysis_date':'2026-09-29'}

def dump(name,x):
 (R/name).write_text(json.dumps(x,indent=2,default=lambda o: o.item() if isinstance(o,np.generic) else str(o)))
def figsave(name):
 plt.tight_layout();plt.savefig(F/(name+'.png'),bbox_inches='tight');plt.close()
def metrics(y,p,t):
 z=p>=t
 return dict(auroc=roc_auc_score(y,p),ap=average_precision_score(y,p),brier=brier_score_loss(y,p),balanced_accuracy=balanced_accuracy_score(y,z),precision=precision_score(y,z,zero_division=0),recall=recall_score(y,z),f1=f1_score(y,z),threshold=t,confusion=confusion_matrix(y,z).tolist())
def effect(fit,name,exp=False):
 b=float(fit.params[name]);lo,hi=fit.conf_int().loc[name]
 return dict(coef=b,effect=float(np.exp(b) if exp else b),lo=float(np.exp(lo) if exp else lo),hi=float(np.exp(hi) if exp else hi),p=float(fit.pvalues[name]))
def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

# Fail fast if the supplied inputs differ from the delivered study's frozen manifest.
frozen=ROOT/'DATA_SHA256.json'
if frozen.exists():
 for name, expected in json.loads(frozen.read_text()).items():
  assert hashfile(ROOT/name)==expected, f'Input changed: {name}; review the study before recomputing.'

print('OULAD preprocessing',flush=True)
p=ROOT/'data/raw/oulad'; key=['code_module','code_presentation','id_student']
i=pd.read_csv(p/'studentInfo.csv');r=pd.read_csv(p/'studentRegistration.csv');a=pd.read_csv(p/'assessments.csv');sa=pd.read_csv(p/'studentAssessment.csv')
assert not i.duplicated(key).any() and not r.duplicated(key).any()
assert not a.id_assessment.duplicated().any() and not sa.duplicated(['id_student','id_assessment']).any()
d=i.merge(r,on=key,validate='one_to_one')
aud={'enrolments_raw':len(i),'unique_students_raw':i.id_student.nunique(),'table_rows':{x.stem:sum(1 for _ in open(x))-1 for x in p.glob('*.csv') if x.stem!='studentVle'},'registration_missing':int(d.date_registration.isna().sum()),'registration_after_day0':int((d.date_registration>0).sum())}
regok=d.date_registration.notna()&(d.date_registration<=0)
aud['removed_registration']=int((~regok).sum());aud['removed_withdrawn_before_landmark']=int((regok & d.date_unregistration.lt(56)).sum())
d=d[regok & (d.date_unregistration.isna() | d.date_unregistration.ge(56))].copy().reset_index(drop=True)
d['risk']=d.final_result.isin(['Fail','Withdrawn']).astype(int);d['season']=d.code_presentation.str[-1];d['context']=d.code_module+'_'+d.season
d['year']=d.code_presentation.str[:4].astype(int)
v=pd.read_csv(p/'studentVle.csv',dtype={'code_module':'category','code_presentation':'category','id_student':'int32','id_site':'int32','date':'int16','sum_click':'int32'})
aud.update(vle_rows_raw=len(v),vle_exact_duplicates=int(v.duplicated().sum()),vle_negative_date_rows=int((v.date<0).sum()),vle_nonpositive=int((v.sum_click<=0).sum()))
# The supplied rows are daily counts; repeated rows are retained, not asserted to be export errors.
assert not v.isna().any().any() and (v.sum_click>=0).all()
v=v[(v.date>=0)&(v.date<168)].copy()
for c in ['code_module','code_presentation']:v[c]=v[c].astype(str)
daily=v.groupby(key+['date'],observed=True).sum_click.sum().reset_index()
daily=daily.merge(d[key],on=key,validate='many_to_one')
early=daily[daily.date<56]
wide=early.pivot(index=key,columns='date',values='sum_click').reindex(columns=range(56),fill_value=0).fillna(0)
wide=wide.reindex(pd.MultiIndex.from_frame(d[key]),fill_value=0)
arr=wide.to_numpy();assert len(arr)==len(d)
d['clicks']=arr.sum(1);d['log_clicks']=np.log1p(d.clicks);d['active_days']=(arr>0).sum(1);d['active7']=d.active_days/7
d['momentum']=np.log1p(arr[:,42:56].sum(1))-np.log1p(arr[:,28:42].sum(1))
d['recency']=55-np.where(arr>0,np.arange(56),-1).max(1)
d['credits60']=d.studied_credits/60
# Count only non-banked, non-exam assessments with deadlines already elapsed and submissions already observed.
banked=sa[sa.is_banked.eq(1)][['id_student','id_assessment']]
due=a[a.assessment_type.ne('Exam') & a.date.between(0,55)]
opp=d[key].merge(due[['code_module','code_presentation','id_assessment','date']],on=['code_module','code_presentation'])
opp=opp.merge(banked.assign(banked=1),on=['id_student','id_assessment'],how='left',validate='many_to_one')
aud['banked_opportunities_removed']=int(opp.banked.eq(1).sum())
opp=opp[opp.banked.isna()].drop(columns='banked')
observed=sa[sa.is_banked.eq(0)&sa.date_submitted.le(55)][['id_student','id_assessment','date_submitted']]
opp=opp.merge(observed,on=['id_student','id_assessment'],how='left',validate='many_to_one')
opp['ontime']=opp.date_submitted.notna() & opp.date_submitted.le(opp.date)
sub=opp.groupby(key).agg(due_n=('id_assessment','size'),ontime_n=('ontime','sum')).reset_index()
d=d.merge(sub,on=key,how='left',validate='one_to_one');d[['due_n','ontime_n']]=d[['due_n','ontime_n']].fillna(0)
d['no_due']=(d.due_n==0).astype(int);d['ontime_share']=(d.ontime_n/d.due_n.replace(0,np.nan)).fillna(0)
aud.update(landmark_n=len(d),zero_early_clicks=int(d.clicks.eq(0).sum()),landmark_outcomes=d.final_result.value_counts().to_dict())
historical=d[d.year==2013].copy();new=d[d.year==2014].copy()
seen=set(i.loc[i.code_presentation.str.startswith('2013'),'id_student'])
aud['test_removed_seen_people']=int(new.id_student.isin(seen).sum());new=new[~new.id_student.isin(seen)]
aud['test_removed_unseen_context']=int((~new.context.isin(historical.context)).sum());test=new[new.context.isin(historical.context)].copy()
tr,va=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SEED).split(historical,groups=historical.id_student))
train=historical.iloc[tr].copy();val=historical.iloc[va].copy()
assert not set(train.id_student)&set(val.id_student)
assert not set(test.id_student)&seen
assert set(test.context)<=set(train.context)
splits={k:{'n':len(z),'students':z.id_student.nunique(),'risk_rate':z.risk.mean()} for k,z in [('train',train),('validation',val),('test',test)]}
base=['log_clicks','num_of_prev_attempts','credits60']
full=base+['active7','momentum','ontime_share','no_due']
# Fit every transformation on training data only. Context combines module with February/October season.
def pipe(model,cols):return make_pipeline(ColumnTransformer([('num',StandardScaler(),cols),('cat',OneHotEncoder(handle_unknown='ignore'),['context'])]),model)
models={'Volume/context LR':pipe(LogisticRegression(C=1,max_iter=3000,random_state=SEED),base),'Behaviour LR':pipe(LogisticRegression(C=1,max_iter=3000,random_state=SEED),full),'Random forest':pipe(RandomForestClassifier(n_estimators=400,min_samples_leaf=20,max_features='sqrt',random_state=SEED,n_jobs=-1),full)}
print('OULAD modeling',splits,flush=True)
mm={};preds={};vv={}
for name,model in models.items():
 model.fit(train,train.risk);pv=model.predict_proba(val)[:,1];pt=model.predict_proba(test)[:,1]
 thresholds=np.linspace(.05,.95,181);scores=[f1_score(val.risk,pv>=t) for t in thresholds];threshold=float(thresholds[np.argmax(scores)])
 mm[name]=metrics(test.risk,pt,threshold);vv[name]=dict(auroc=roc_auc_score(val.risk,pv),ap=average_precision_score(val.risk,pv),f1=max(scores),threshold=threshold);preds[name]=pt
prev=float(train.risk.mean());mm['Prevalence dummy']=metrics(test.risk,np.full(len(test),prev),.5)
selected=max(vv,key=lambda n:vv[n]['ap'])
# Person-clustered bootstrap preserves repeated enrolments; paired differences share resamples.
groups=[np.flatnonzero(test.id_student.to_numpy()==u) for u in test.id_student.unique()]
boot={n:[] for n in preds};diff=[]
y=test.risk.to_numpy()
for b in range(1000):
 idx=np.concatenate([groups[j] for j in rng.integers(0,len(groups),len(groups))])
 if np.unique(y[idx]).size<2:continue
 for n,pred in preds.items():boot[n].append(roc_auc_score(y[idx],pred[idx]))
 diff.append(boot['Behaviour LR'][-1]-boot['Volume/context LR'][-1])
for n in preds:mm[n]['auroc_ci']=np.quantile(boot[n],[.025,.975]).tolist()
auc_delta={'effect':mm['Behaviour LR']['auroc']-mm['Volume/context LR']['auroc'],'ci':np.quantile(diff,[.025,.975]).tolist()}
# Held-out inference is exploratory; prediction models above are not refit/tuned using these outcomes.
formula='risk ~ log_clicks + active7 + momentum + num_of_prev_attempts + credits60 + ontime_share + no_due + C(context)'
# no_due is constant in some cohorts, so remove only if constant (unidentifiable coefficient).
if test.no_due.nunique()==1:formula=formula.replace(' + no_due','')
infer=smf.glm(formula,data=test,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':test.id_student})
oh={'O1':effect(infer,'active7',True),'O2':effect(infer,'momentum',True)}
# Descriptive whole-landmark trajectories, separately from prediction cohorts.
weekly=daily.assign(week=lambda z:z.date//7).groupby(key+['week']).sum_click.sum().unstack('week').reindex(columns=range(24),fill_value=0).fillna(0)
weekly=weekly.reindex(pd.MultiIndex.from_frame(d[key]),fill_value=0)
fig,ax=plt.subplots(1,2,figsize=(10.8,3.4))
traj=[]
for j,(label,color) in enumerate([('Pass/Distinction',COL[0]),('Fail/Withdrawn',COL[1])]):
 vals=weekly.to_numpy()[d.risk.eq(j)];mean=vals.mean(0);active=(vals>0).mean(0)
 for w in range(24):traj.append(dict(group=label,week=w+1,mean_clicks=mean[w],active_fraction=active[w],n=len(vals)))
 ax[0].plot(range(1,25),mean,label=label,color=color,lw=2);ax[1].plot(range(1,25),active*100,label=label,color=color,lw=2)
for aa in ax:aa.axvline(8.5,color='gray',ls='--');aa.set_xlabel('Week from course start');aa.grid(alpha=.2)
ax[0].set(ylabel='Mean clicks per enrolled learner',title='Activity volume');ax[1].set(ylabel='Learners with recorded activity (%)',title='Participation coverage',ylim=(0,105));ax[0].legend(fontsize=10)
figsave('oulad_trajectories');pd.DataFrame(traj).to_csv(R/'oulad_weekly_aggregate.csv',index=False)
fig,ax=plt.subplots(1,2,figsize=(10.8,3.4))
for n,pred in preds.items():
 fpr,tpr,_=roc_curve(y,pred);ax[0].plot(fpr,tpr,label=f'{n}: {mm[n]["auroc"]:.3f}')
 prec,rec,_=precision_recall_curve(y,pred);ax[1].plot(rec,prec,label=f'{n}: {mm[n]["ap"]:.3f}')
ax[0].plot([0,1],[0,1],'--',color='gray');ax[1].axhline(y.mean(),color='gray',ls='--',label=f'Test prevalence: {y.mean():.3f}')
ax[0].set(xlabel='False positive rate',ylabel='True positive rate',title='ROC curves, 2014 test');ax[1].set(xlabel='Recall',ylabel='Precision',title='Precision-recall curves, 2014 test')
for aa in ax:aa.legend(fontsize=10);aa.grid(alpha=.15)
figsave('oulad_model_curves')
# Calibration, subgroup model performance and cohort sizes are aggregate-only.
subgroup=[]
for col in ['code_module','season','gender','disability']:
 for valn,idx in test.groupby(col).indices.items():
  yy=y[idx];pp=preds[selected][idx]
  if len(np.unique(yy))==2:subgroup.append({'dimension':col,'group':valn,'n':len(idx),**metrics(yy,pp,mm[selected]['threshold'])})
pd.DataFrame(subgroup).to_csv(R/'oulad_subgroup_metrics.csv',index=False)
d.to_csv(PRIVATE/'oulad_features.csv',index=False)
check=test[['id_student','risk']].reset_index(drop=True).copy()
for name, pred in preds.items(): check[name]=pred
check.to_csv(PRIVATE/'oulad_test_predictions.csv',index=False)
res['oulad']={'audit':aud,'splits':splits,'models':mm,'validation':vv,'selected_by_validation_ap':selected,'auc_delta':auc_delta,'hypotheses':oh,'inference_formula':formula,'contexts':sorted(test.context.unique().tolist())}
dump('results.json',res)

print('Moodle preprocessing',flush=True)
raw=pd.read_csv(ROOT/'data/raw/moodle/moodle.csv');raw_n=len(raw);dup=int(raw.duplicated().sum());raw=raw.drop_duplicates().copy()
raw['t']=pd.to_datetime(raw.Time,format='%d/%m/%y, %H:%M:%S',errors='coerce')
assert raw.t.notna().all() and raw['User ID'].notna().all()
anchor=raw.t.min().normalize();raw['day']=(raw.t.dt.normalize()-anchor).dt.days;raw['week']=raw.day//7
raw['user']=raw['User ID']
telemetry=['Quiz attempt auto-saved','Submitted SCORM raw score','Submitted SCORM status']
x=raw[~raw['Event name'].isin(telemetry)].copy();first=x.groupby('user').day.min();users=first[first<28].index
x=x[x.user.isin(users)].copy();early=x[x.day<56].copy();later=x[x.day.between(56,83)].copy()
assert early.day.max()<later.day.min()

def moodle_features(events,cohort):
 e=events[events.day<56].copy();g=e.groupby('user');z=pd.DataFrame(index=cohort)
 z['events']=g.size();z['active_days']=g.day.nunique();z['log_events']=np.log1p(z.events);z['active7']=z.active_days/7
 z['arrival_week']=g.day.min()/7;z['recency']=55-g.day.max()
 cc=e[e.Component.ne('System')].groupby(['user','Component']).size().unstack(fill_value=0).reindex(cohort,fill_value=0)
 probs=cc.div(cc.sum(1).replace(0,np.nan),axis=0).fillna(0)
 z['entropy']=-(probs*np.log(probs.where(probs>0,1))).sum(1)
 z['quiz_share']=e.Component.eq('Quiz').groupby(e.user).sum().reindex(cohort,fill_value=0)/z.events
 z['content_share']=e.Component.isin(['Book','File','Page','SCORM package','Glossary']).groupby(e.user).sum().reindex(cohort,fill_value=0)/z.events
 return z.fillna(0)
m=moodle_features(x,users)
m['future_days']=later.groupby('user').day.nunique().reindex(users,fill_value=0);m['future_weeks']=later.groupby('user').week.nunique().reindex(users,fill_value=0)
fit=smf.ols('future_days ~ active7 + log_events + entropy + arrival_week',data=m).fit(cov_type='HC3')
mh={'M1':effect(fit,'active7'),'M2':effect(fit,'entropy')}
# Bootstrap per person as a small-sample sensitivity to the HC3 interval.
bs={k:[] for k in ['active7','entropy']}
for b in range(2000):
 mb=m.iloc[rng.integers(0,len(m),len(m))]
 fb=smf.ols('future_days ~ active7 + log_events + entropy + arrival_week',data=mb).fit()
 for k in bs:bs[k].append(fb.params[k])
for h,k in [('M1','active7'),('M2','entropy')]:mh[h]['bootstrap_ci']=np.quantile(bs[k],[.025,.975]).tolist()
# Telemetry sensitivity uses the same selected users and anchor; outcomes count active days in raw follow-up.
ms=moodle_features(raw[raw.user.isin(users)],users);ms['future_days']=raw[raw.user.isin(users)&raw.day.between(56,83)].groupby('user').day.nunique().reindex(users,fill_value=0)
fs=smf.ols('future_days ~ active7 + log_events + entropy + arrival_week',data=ms).fit(cov_type='HC3')
tele_sens={'M1':effect(fs,'active7'),'M2':effect(fs,'entropy')}
# Gap-based sessions; zero terminal padding. Equal-time events contribute zero duration.
session_stats=[]
session_feature={}
for minutes in [15,30,60]:
 e=early.sort_values(['user','t']).copy();gap=e.groupby('user').t.diff().dt.total_seconds()/60
 e['new']=gap.isna() | gap.gt(minutes);e['sid']=e.groupby('user')['new'].cumsum();e['duration']=gap.where(~e.new,0)
 sess=e.groupby(['user','sid']).agg(duration=('duration','sum'),events=('t','size'))
 session_stats.append({'gap_minutes':minutes,'sessions':len(sess),'singleton_fraction':float(sess.events.eq(1).mean()),'median_session_minutes':float(sess.duration.median()),'mean_session_minutes':float(sess.duration.mean()),'total_observed_hours':float(sess.duration.sum()/60)})
 session_feature[minutes]=sess.groupby(level=0).duration.sum().reindex(users,fill_value=0)
m['observed_minutes30']=session_feature[30]
print('Moodle clustering',len(m),flush=True)
features=['log_events','active_days','entropy','quiz_share'];sc=StandardScaler();Z=sc.fit_transform(m[features])
ks=[];kms={}
for k in range(2,6):
 km=KMeans(n_clusters=k,n_init=50,random_state=SEED).fit(Z);s=silhouette_score(Z,km.labels_);ks.append({'k':k,'silhouette':s,'inertia':km.inertia_});kms[k]=km
best=max(ks,key=lambda z:z['silhouette'])['k'];km=kms[best]
# Stable numeric labels sorted by early activity, without using future data.
order=m.assign(old=km.labels_).groupby('old').events.median().sort_values().index
mapping={old:new for new,old in enumerate(order)};m['cluster']=[mapping[l] for l in km.labels_]
stability=[]
for b in range(200):
 idx=rng.integers(0,len(m),len(m));scb=StandardScaler().fit(m.iloc[idx][features]);zb=scb.transform(m[features])
 kmb=KMeans(n_clusters=best,n_init=20,random_state=SEED+b).fit(zb[idx]);stability.append(adjusted_rand_score(km.labels_,kmb.predict(zb)))
profiles=m.groupby('cluster').agg(n=('events','size'),events=('events','median'),active_days=('active_days','median'),entropy=('entropy','median'),quiz_share=('quiz_share','median'),future_days=('future_days','median'),future_weeks=('future_weeks','median'),minutes30=('observed_minutes30','median')).reset_index()
kw=st.kruskal(*[z.future_days.to_numpy() for _,z in m.groupby('cluster')]);eps=max(0,(kw.statistic-best+1)/(len(m)-best))
profiles.to_csv(R/'moodle_cluster_profiles.csv',index=False);pd.DataFrame(ks).to_csv(R/'moodle_k_selection.csv',index=False)
# Calendar-aligned descriptive chart retains zero-user weeks, constant denominator.
weekly=x.groupby(['user','week']).size().unstack(fill_value=0).reindex(index=users,columns=range(16),fill_value=0)
fig,ax=plt.subplots(1,2,figsize=(10.8,3.5));rows=[]
for c,z in m.groupby('cluster'):
 w=weekly.loc[z.index];mean=w.mean(0);coverage=(w>0).mean(0)*100
 ax[0].plot(range(1,17),mean,lw=2,label=f'Profile {c+1} (n={len(z)})',color=COL[c]);ax[1].plot(range(1,17),coverage,lw=2,color=COL[c])
 for week in range(16):rows.append({'profile':int(c+1),'week':week+1,'mean_events':float(mean[week]),'active_percent':float(coverage[week]),'n':len(z)})
for aa in ax:
 aa.axvline(8.5,ls='--',color='gray');aa.axvspan(8.5,12.5,alpha=.08,color=COL[0]);aa.set_xlabel('Week from first observed date');aa.grid(alpha=.15)
ax[0].set(ylabel='Mean filtered events per user',title='Volume by early profile');ax[0].legend(fontsize=10)
ax[1].set(ylabel='Users with recorded activity (%)',title='Participation by early profile',ylim=(0,105))
figsave('moodle_trajectories');pd.DataFrame(rows).to_csv(R/'moodle_weekly_aggregate.csv',index=False)
fig,ax=plt.subplots(1,2,figsize=(10.8,3.4))
heat=pd.DataFrame(Z,columns=features).assign(cluster=m.cluster.to_numpy()).groupby('cluster').mean();heat.index=['Profile '+str(i+1) for i in heat.index];heat.columns=['Log events','Active days','Diversity','Quiz share']
sns.heatmap(heat,annot=True,fmt='.2f',cmap='vlag',center=0,ax=ax[0],cbar_kws={'label':'Mean standardized value'});ax[0].set(title='Early profile characteristics',ylabel='');ax[0].tick_params(axis='x',rotation=15)
sns.boxplot(data=m.assign(Profile=m.cluster+1),x='Profile',y='future_days',ax=ax[1],color='#ABD2DD',showfliers=False);sns.stripplot(data=m.assign(Profile=m.cluster+1),x='Profile',y='future_days',ax=ax[1],color='#203747',alpha=.4,jitter=.18,size=3);ax[1].set(title='External follow-up: weeks 9-12',ylabel='Active days (out of 28)');ax[1].grid(axis='y',alpha=.2)
figsave('moodle_profiles')
# Calendar event composition for all users, not just early-arrival cohort.
allclean=raw[~raw['Event name'].isin(telemetry)].copy()
comp=pd.crosstab(allclean.week,allclean.Component).reindex(range(raw.week.max()+1),fill_value=0)
comp.to_csv(R/'moodle_weekly_components.csv')
fig,ax=plt.subplots(figsize=(10.8,2.7))
for cname in ['Quiz','Book','SCORM package','Assignment','Forum']:
 ax.plot(comp.index+1,comp[cname],label=cname,lw=1.7)
ax.set(xlabel='Week from 23 Oct 2025',ylabel='Filtered event count',title='Moodle course activity mix: all 174 observed IDs');ax.legend(ncol=5,fontsize=10);ax.grid(alpha=.15)
figsave('moodle_components')
m.to_csv(PRIVATE/'moodle_features.csv')
res['moodle']={'audit':{'raw_events':raw_n,'raw_users':raw.user.nunique(),'duplicates':dup,'bad_timestamps':int(raw.t.isna().sum()),'missing_content_code':int(raw['Content code'].isna().sum()),'telemetry_removed':int(raw['Event name'].isin(telemetry).sum()),'filtered_all_events':len(allclean),'filtered_cohort_events':len(x),'early_events':len(early),'followup_events':len(later),'cohort_n':len(m),'late_arrival_excluded':raw.user.nunique()-len(m),'anchor':str(anchor.date()),'last_date':str(raw.t.max()),'cutoff':str((anchor+pd.Timedelta(days=56)).date()),'followup_end':str((anchor+pd.Timedelta(days=83)).date()),'future_zero_users':int(m.future_days.eq(0).sum()),'forum_posts':int(raw['Event name'].eq('Some content has been posted.').sum())},'hypotheses':mh,'ols_r2':fit.rsquared,'k_selection':ks,'selected_k':best,'stability_median':float(np.median(stability)),'stability_interval':np.quantile(stability,[.025,.975]).tolist(),'profiles':profiles.to_dict('records'),'followup_kruskal':{'H':kw.statistic,'p':kw.pvalue,'epsilon_squared':eps},'sessions':session_stats,'telemetry_sensitivity':tele_sens,'feature_correlations':m[features+['future_days']].corr().round(3).to_dict()}
# Family-wise correction across the four pre-specified associations.
hs=[oh['O1'],oh['O2'],mh['M1'],mh['M2']];padj=multipletests([h['p'] for h in hs],method='holm')[1]
for h,pv in zip(hs,padj):h['p_holm']=float(pv)
res['hypothesis_decisions']={k:bool(h['p_holm']<.05 and np.sign(h['coef'])==sgn) for k,h,sgn in zip(['O1','O2','M1','M2'],hs,[-1,-1,1,1])}
# O2 expects higher momentum to reduce risk (negative coefficient).
manifest={str(p.relative_to(ROOT)):hashfile(p) for p in sorted((ROOT/'data/raw/oulad').glob('*.csv'))}
manifest['data/raw/moodle/moodle.csv']=hashfile(ROOT/'data/raw/moodle/moodle.csv')
dump('input_sha256.json',manifest);dump('results.json',res)
# Summary figure of adjusted effects, different axes avoid mixing odds ratios and active days.
fig,ax=plt.subplots(1,2,figsize=(10.8,2.8))
for aa,items,labels,null,xlabel in [(ax[0],[oh['O1'],oh['O2']],['O1: +7 active days','O2: +1 log momentum'],1,'Adjusted odds ratio for Fail/Withdrawn'),(ax[1],[mh['M1'],mh['M2']],['M1: +7 active days','M2: +1 diversity nat'],0,'Adjusted change in later active days')]:
 for j,h in enumerate(items):aa.errorbar(h['effect'],j,xerr=[[h['effect']-h['lo']],[h['hi']-h['effect']]],fmt='o',color=COL[j],capsize=4)
 aa.set_yticks([0,1],labels);aa.axvline(null,color='gray',ls='--');aa.set_xlabel(xlabel);aa.set_ylim(-.7,1.7);aa.grid(axis='x',alpha=.15)
figsave('hypothesis_effects')
print(json.dumps({'decisions':res['hypothesis_decisions'],'oulad_models':mm,'oulad_hypotheses':oh,'moodle_hypotheses':mh,'moodle_n':len(m),'k':best,'profiles':profiles.to_dict('records')},indent=2),flush=True)
