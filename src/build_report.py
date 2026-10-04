"""Build the cohesive ten-page assignment PDF from computed aggregate results."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/results.json').read_text());b=json.loads((ROOT/'results/robustness.json').read_text())
o=r['oulad'];m=r['moodle'];out=ROOT/'output/pdf/Learning_Behaviour_Analytics_Report.pdf'
REPO='https://github.com/luffy-taro-106/learning-behaviour-analytics'
NAVY=colors.HexColor('#142E40');TEAL=colors.HexColor('#176B87');GRAY=colors.HexColor('#536471');PALE=colors.HexColor('#EAF2F5');ORANGE=colors.HexColor('#D55E00')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=10.2,leading=14,spaceAfter=7,textColor=NAVY))
styles.add(ParagraphStyle(name='SmallX',fontName='Helvetica',fontSize=8.5,leading=11.5,spaceAfter=5,textColor=GRAY))
styles.add(ParagraphStyle(name='H1X',fontName='Helvetica-Bold',fontSize=22,leading=26,spaceAfter=13,textColor=NAVY))
styles.add(ParagraphStyle(name='H2X',fontName='Helvetica-Bold',fontSize=12.4,leading=16,spaceBefore=8,spaceAfter=6,textColor=TEAL))
styles.add(ParagraphStyle(name='TitleX',fontName='Helvetica-Bold',fontSize=36,leading=40,textColor=NAVY,spaceAfter=16))
styles.add(ParagraphStyle(name='DeckX',fontName='Helvetica',fontSize=16,leading=22,textColor=TEAL,spaceAfter=18))
styles.add(ParagraphStyle(name='TableX',fontName='Helvetica',fontSize=8.8,leading=11.5,textColor=NAVY))
styles.add(ParagraphStyle(name='TableHead',fontName='Helvetica-Bold',fontSize=8.8,leading=11.5,textColor=colors.white))
W,H=A4;PW=W-84
story=[]
def p(s,kind='BodyX'):story.append(Paragraph(s,styles[kind]))
def h(s):p(s,'H2X')
def title(num,s):p(num.upper(),'SmallX');p(s,'H1X')
def table(rows,widths,header=True):
 cells=[[Paragraph(str(v),styles['TableHead' if header and i==0 else 'TableX']) for v in row] for i,row in enumerate(rows)]
 t=Table(cells,colWidths=[PW*x for x in widths],hAlign='LEFT')
 cmds=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#B9CBD4'))]
 if header:cmds += [('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE])]
 else:cmds += [('BACKGROUND',(0,0),(-1,-1),PALE)]
 t.setStyle(TableStyle(cmds));story.append(t);story.append(Spacer(1,8))
def figure(name,caption,max_h=None):
 path=ROOT/'figures'/f'{name}.png';im=PILImage.open(path);w=PW;ht=w*im.height/im.width
 if max_h and ht>max_h:w*=max_h/ht;ht=max_h
 story.append(Image(str(path),width=w,height=ht,hAlign='CENTER'));p(caption,'SmallX')
def page():story.append(PageBreak())
def fmt(x):return f'{x:.3f}'
def footer(c,doc):
 c.saveState()
 if doc.page>1:
  c.setStrokeColor(TEAL);c.setLineWidth(.7);c.line(42,H-32,W-42,H-32)
  c.setFillColor(GRAY);c.setFont('Helvetica',8);c.drawString(42,H-25,'LEARNING BEHAVIOUR ANALYTICS  |  OULAD + MOODLE')
 c.setFillColor(GRAY);c.setFont('Helvetica',8);c.drawString(42,25,'ET 610  |  Darshan Sonawane, Aditya Singh, Ashok Kumar');c.drawRightString(W-42,25,f'{doc.page} / 10');c.restoreState()

# 1: title, introduction and hypotheses; preserves room for a dedicated contributions page.
p('ET 610 / GROUP ASSIGNMENT','SmallX')
p('Beyond click counts','H1X')
p('Temporal engagement, learner profiles and early risk in OULAD and Moodle','DeckX')
table([['Team member','Roll number'],['Darshan Sonawane','23b1541'],['Aditya Singh','23b1524'],['Ashok Kumar','23b0628']],[.64,.36])
h('01 / Introduction & hypotheses')
p('Do the timing and spread of engagement reveal more than click volume? Motivated by distributed practice [4], this study separates activity spread, recent momentum and resource diversity. OULAD supplies final course outcomes; Moodle supports later observed participation, with no grade or enrolment roster. An active LMS day is a behavioural trace, not a validated measure of self-regulation. The datasets are analyzed separately.')
table([['ID / mechanism','Directional hypothesis and operational test'],['O1 / distributed engagement','At equal early click volume, course context, workload and submission completion, seven additional active days in days 0-55 are associated with lower subsequent Fail/Withdrawn odds.'],['O2 / recent disengagement','A lower log ratio of clicks in weeks 7-8 versus weeks 5-6 is associated with higher subsequent Fail/Withdrawn odds, including adjustment for activity spread.'],['M1 / habit formation','Seven additional active days in the first eight observed weeks are associated with more active days in weeks 9-12, after adjusting for event volume, arrival timing and resource diversity.'],['M2 / resource breadth','Greater Shannon diversity of non-System component use in the first eight weeks is associated with more active days in weeks 9-12, after adjusting for volume, activity spread and arrival timing.']],[.25,.75])
p('The protocol was specified after schema and coverage inspection, before outcome fitting. The analysis is exploratory, not preregistered. Hypotheses require the proposed direction and Holm-adjusted significance across four two-sided tests; effects have 95% confidence intervals. Prediction and association answer different questions, and no causal effect is claimed.','SmallX')
p('Analysis date: 29 September 2026. Team-contribution page added: 4 October 2026.','SmallX')
p(f'Code and aggregate results: <link href="{REPO}" color="#176B87">github.com/luffy-taro-106/learning-behaviour-analytics</link>','SmallX')

# 2: separate team contributions page
page();title('Project details & team','Individual contributions')
h('Project title')
p('<b>Beyond click counts: Temporal engagement, learner profiles and early risk in OULAD and Moodle</b>')
p('The project work is divided into three equally weighted parts, with one part allocated to each team member. Each member has a <b>one-third share</b> of the total contribution. The allocation below covers research design, preparation of both datasets, analysis, evaluation and the final deliverables.')
table([['Team member','Roll number','Contribution share'],['Darshan Sonawane','23b1541','1/3 (equal share)'],['Aditya Singh','23b1524','1/3 (equal share)'],['Ashok Kumar','23b0628','1/3 (equal share)']],[.43,.23,.34])
h('Part 1 / Darshan Sonawane - 23b1541')
p('<b>Research design, data preparation and feature engineering</b>')
p('Formulation of the four domain-informed research hypotheses; review of dataset documentation; acquisition and inspection of OULAD and Moodle data; checks for missing values, duplicate records and valid joins; definition of cohort eligibility, observation windows and sessionization rules; engineering of activity-volume, active-day, momentum, submission and resource-diversity features.')
h('Part 2 / Aditya Singh - 23b1524')
p('<b>Machine learning, statistical evaluation and robustness</b>')
p('Design of the OULAD training, validation and test split; implementation of baseline, logistic-regression and random-forest models; Moodle K-Means segmentation and selection of cluster count; calculation of prediction and clustering metrics; adjusted hypothesis tests, confidence intervals and Holm correction; bootstrap stability, duplicate-row, outcome-definition and telemetry sensitivity analyses.')
h('Part 3 / Ashok Kumar - 23b0628')
p('<b>Visual analytics, interpretation and report preparation</b>')
p('Creation of temporal engagement charts, model-performance plots, learner-profile visualizations and effect-size figures; interpretation of results against the hypotheses; synthesis of course-design implications and study limitations; preparation and formatting of the cohesive PDF report, references and appendix; organization of the reproducible code repository and documentation; final consistency checks and visual review of the report.')
p('Contribution allocation: one-third + one-third + one-third = the complete project.','SmallX')

# 3 data
page();title('02 / Dataset & preprocessing','Two datasets, two outcome definitions')
table([['Source / unit','Raw coverage','Analysis cohort'],['OULAD [1,2]<br/>Student x course run','32,593 enrolments; 28,785 people; 22 presentations; 10,655,280 VLE rows. Seven related CSV tables downloaded from the specified Kaggle mirror.','26,304 enrolments registered by day 0 and still enrolled at day 56. 760 have no early clicks and remain in the analysis.'],['Moodle [3]<br/>Observed user ID','146,048 events, 174 IDs; 23 Oct 2025 to 29 Jul 2026. Fields include time, user, component, event, context and content code.','141 IDs first observed before day 28. After telemetry filtering: 26,376 early events and 18,929 follow-up events. No grade or roster table.']],[.23,.39,.38])
h('OULAD: joins, eligibility and repeated counts')
p('Join registration to student information on student, module and presentation; both composite keys are unique. Assessment IDs uniquely identify assessment metadata. Remove 279 enrolments with missing registration dates (45) or registration after day 0 (234), then 6,010 that withdrew before day 56. Retain later withdrawals as outcomes. The positive class is <b>Fail or Withdrawn</b>; Pass and Distinction form the negative class.')
p('Use days 0-55 for features; ignore pre-course clicks. Aggregate supplied VLE counts to learner-day. There are 787,170 exact repeated VLE rows; no event identifier establishes that these are export errors. Primary analysis retains their counts, while a secondary deduplication analysis checks robustness (p. 9). There are no missing VLE cells or nonpositive click counts. Do not fabricate minute-level sessions from daily counts.')
h('Moodle: chronology, filtering and observation limits')
p('Parse timestamps with the explicit format day/month/two-digit-year, hour:minute:second; all parse successfully and no full rows are duplicated. Preserve the export clock because its timezone is unspecified. Remove 40,826 auto-save and SCORM score/status telemetry events, leaving 105,222 events across all observed IDs. Keep navigation and user-facing events. Content code is missing in 35,493 rows; no imputation is needed because component-based features do not use that field.')
p('Anchor day 0 at midnight on 23 October 2025, the first observed date, <b>not a verified course start</b>. Early window: 23 October-17 December; follow-up: 18 December-14 January. Exclude 33 late-arriving IDs from cohort models. No role field is available, so IDs are proxies for learners and staff contamination cannot be ruled out. The two supplemental Drive folders were inspected; their task-level schema/IDs do not establish a join to this export, so they are not pooled [6].')

# 4 features
page();title('03 / Feature extraction','Measure only what was observable')
table([['Feature','Definition and purpose'],['Volume (both)','OULAD: log(1 + sum of clicks on days 0-55). Moodle: log(1 + filtered event count in the same 56-day window). Log transforms reduce the influence of extreme counts.'],['Activity spread (both)','Number of distinct days with at least one positive click/event, including zero-activity learners where a roster exists. Dividing by 7 makes regression effects interpretable per seven additional active days.'],['OULAD momentum','log(1 + clicks on days 42-55) - log(1 + clicks on days 28-41). Negative values indicate declining recent activity. Both windows contain 14 days; +1 permits zero counts.'],['OULAD on-time share','On-time observed submissions / eligible non-exam assessments due by day 55. Exclude banked assessments from numerator and denominator (893 opportunities). Only submissions observed by day 55 can count; zero eligible assessments get share 0 plus a separate no-due flag.'],['OULAD context controls','Module x presentation-season category, number of prior attempts, and studied credits / 60. Final result is the target; withdrawal dates determine eligibility only. Scores and demographics are not predictor inputs.'],['Moodle diversity / quiz share','H = -sum p(c) log p(c), in nats, over non-System component counts; H=0 when there are no such events. Quiz share = Quiz events / all filtered events. The taxonomy, not content mastery, defines breadth.'],['Moodle timing / follow-up','Arrival timing = first observed day / 7. Follow-up active days range from 0 to 28; follow-up active weeks from 0 to 4. These outcomes are excluded from clustering inputs.']],[.26,.74])
h('Sessionization and observed duration')
p('Within each Moodle user, sort retained early events by timestamp. Start a new session if the gap from the previous event exceeds 30 minutes. Sum gaps only inside sessions; add no terminal duration after the last event. Equal-time events add zero, and single-event sessions have zero observed duration. This is a <b>duration proxy</b>, not verified time-on-task: idle tabs and offline study remain invisible [5]. Repeat with 15- and 60-minute gaps.')
h('Preventing future information from entering models')
p('All predictors end before day 56. OULAD’s outcome is the final course result; Moodle’s outcome starts on day 56. Count missing learner-weeks as zero within a fixed selected cohort. Fit OULAD scaling and category encoding on training data only. In Moodle, standardize four early features for descriptive clustering; future days are used only after clusters have been formed.')

# 5 temporal
page();title('04 / Temporal behavioural visualizations','Volume and coverage tell different stories')
figure('oulad_trajectories','<b>Figure 1.</b> OULAD landmark cohort: Pass/Distinction n=15,266; Fail/Withdrawn n=11,038. Dashed line marks the end of the feature window. Cohort denominators remain fixed, including zero-activity weeks; post-cutoff trajectories are descriptive and never predictors.')
p('By week 8, recorded activity covers 85.9% of the eventual Pass/Distinction group and 58.0% of Fail/Withdrawn. By week 24 this is 81.7% versus 21.2%. The widening separation is compatible with disengagement, but later withdrawals mechanically contribute zeros. The common week-12 dip also warns against reading every decline as an individual problem.')
figure('moodle_trajectories','<b>Figure 2.</b> Moodle profiles defined solely from weeks 1-8; n=57, 78 and 6. Shading marks follow-up weeks 9-12. Coverage uses the full profile denominator, and event means include zeros. The observation anchor is 23 October 2025.')
p('In Moodle week 12, the small quiz-focused profile averages 137.8 events per user but only 66.7% are active; the broadly active profile averages 35.8 events with 70.5% active. A large mean therefore need not imply broader participation. Later spikes may reflect assessment schedules, but due dates are unavailable and cannot be inferred from event peaks.')

# 6 supervised
page();title('05 / Machine learning & results','OULAD: forward-in-time risk prediction')
p('Split eligible 2013 enrolments by student using an 80/20 grouped holdout (seed 610): <b>9,101 training</b> and <b>2,267 validation</b>. Test on <b>9,683 2014 enrolments</b> from 9,579 people: exclude 1,442 enrolments whose person appeared anywhere in 2013 and 3,811 with unseen module-season combinations. Test prevalence is 38.3%. This estimates performance for new students in known contexts, not for unseen modules.')
p('Compare a prevalence dummy, L2 logistic regression (C=1), enhanced behaviour LR, and a random forest (400 trees, minimum leaf 20, square-root feature sampling). Both enhanced models use all OULAD features on p. 4. Hyperparameters are fixed. Select the classifier by validation average precision (AP); select each classification threshold by validation F1 on a 0.05-0.95 grid with step 0.005. No test tuning or train-validation refit.')
rows=[['Model','AUROC [95% CI]','AP','Brier','F1']]
for name in ['Prevalence dummy','Volume/context LR','Behaviour LR','Random forest']:
 z=o['models'][name];ci=z.get('auroc_ci');rows.append([name,fmt(z['auroc'])+(f' [{ci[0]:.3f}, {ci[1]:.3f}]' if ci else ''),fmt(z['ap']),fmt(z['brier']),fmt(z['f1'])])
table(rows,[.27,.31,.14,.14,.14])
figure('oulad_model_curves','<b>Figure 3.</b> Held-out 2014 discrimination. AP is average precision, not trapezoidal PR area. AUROC intervals use 1,000 person-cluster bootstrap resamples. Lower Brier score is better. The dummy predicts the training prevalence.',max_h=175)
p('<b>Selected random forest:</b> validation AP 0.762; test AUROC 0.775 [0.765, 0.784]. At threshold 0.37, precision=0.574, recall=0.724, balanced accuracy=0.696 and F1=0.641. The confusion matrix has TN=3,991, FP=1,988, FN=1,021 and TP=2,683. About 43% of flagged enrolments are false positives, which argues for supportive, low-cost outreach rather than punitive action.')
p('Behaviour LR improves AUROC over the volume/context baseline by 0.045 [0.037, 0.053], using a paired person bootstrap. This is the gain from the whole behaviour bundle, including submissions; the temporal-only ablation on p. 9 separates that contribution. Brier scores quantify overall probability error, but do not alone establish calibration.','SmallX')

# 7 clustering
page();title('05 / Machine learning & results','Moodle: three early engagement profiles')
p('Apply K-Means to standardized log events, active days, component diversity and quiz share for all 141 early-arriving users. Use 50 initializations and seed 610. This is <b>unsupervised descriptive segmentation</b>, so there is no grade prediction accuracy or artificial train/test score. Select k from 2-5 by silhouette using early features only; later participation is an external comparison.')
table([['k','2','3 (selected)','4','5'],['Silhouette','0.361','0.421','0.409','0.405']],[.24,.19,.19,.19,.19])
figure('moodle_profiles','<b>Figure 4.</b> Left: standardized profile means. Right: later active days; boxes show median and IQR, whiskers extend to 1.5 IQR and points show all users. Label numbers are ordered by median early events, not future outcomes.',max_h=180)
table([['Profile (n)','Early events','Active days','Diversity','Quiz share','Later days'],['1: sparse (57)','32','4','0.451','0%','2'],['2: broadly active (78)','222.5','13','1.251','0%','5'],['3: quiz-focused (6)','264.5','8.5','0.747','43.2%','4']],[.26,.15,.15,.15,.14,.15])
p('Table entries are medians except sample size. Profile 2 combines more visits across days with greater breadth. Profile 3 is distinct mainly in quiz share, not a universal high-engagement category. The median quiz share of zero in profiles 1 and 2 does not mean every member avoided quizzes.')
p('Refit preprocessing and K-Means on 200 user bootstrap samples, then label all original users: median adjusted Rand index is <b>0.919</b>, but the 2.5th-97.5th percentile range is <b>0.417-1.000</b>. This broad range and the six-user profile limit stability claims. Standardizing a rare quiz-share feature can amplify this small group.')
p('Future active days differ across profiles (Kruskal-Wallis H=17.468, df=2, p=0.000161; epsilon-squared=0.112). This is an exploratory omnibus comparison, not evidence that each profile pair differs or that cluster membership causes persistence. Subsequent activity was never used to choose k. Sixteen cohort users had no follow-up event.')

# 8 inference
page();title('05 / Hypothesis evaluation','Three associations supported; one unresolved')
figure('hypothesis_effects','<b>Figure 5.</b> Adjusted effects with pointwise 95% intervals. OULAD: odds ratios, null=1. Moodle: additional future active days, null=0. Different axes reflect different outcomes and must not be compared numerically.',max_h=160)
table([['Hypothesis','Adjusted effect [95% CI]','Holm p','Conclusion'],['O1: +7 active days','OR 0.779 [0.744, 0.816]','9.44 x 10<super>-26</super>','Supported'],['O2: +1 log momentum','OR 0.911 [0.883, 0.940]','1.44 x 10<super>-8</super>','Supported'],['M1: +7 active days','+1.822 days [1.057, 2.586]','0.00000601','Supported'],['M2: +1 diversity nat','-0.937 days [-2.236, 0.362]','0.158','Not supported']],[.27,.39,.17,.17])
h('OULAD: spread and momentum contribute separately')
p('Fit a separate binomial-logit association model to the 2014 test cohort, including both hypothesis features, log clicks, prior attempts, credits, on-time share, no-due flag and module-season fixed effects. Use person-clustered standard errors for repeated enrolments. O1 corresponds to approximately 22.1% lower adjusted odds per seven additional active days, not a 22.1 percentage-point reduction in risk. For O2, a one-unit lower log momentum corresponds to about 1/0.911=1.098 times the odds, consistent with a recent decline signal.')
p('This inferential fit uses held-out outcomes only to estimate exploratory associations; it does not change the trained prediction models. Conditional associations can still reflect prior ability, motivation, access or course design. The dataset does not directly observe self-regulatory strategies.')
h('Moodle: breadth is not an independent positive signal')
p('OLS models later active days using active days/7, log events, diversity and arrival timing, with HC3 standard errors (R-squared=0.307). M1’s person-bootstrap interval is [1.088, 2.588] additional days. M2’s interval spans zero, and its estimate is opposite the proposed direction. The data therefore fail to support M2; they do not prove breadth has no value.')
p('Diversity has a positive unadjusted correlation with future days (r=0.211) but also correlates with log event volume (r=0.707). The adjusted result shows why visually richer activity profiles cannot establish a separate breadth effect. Holm correction covers the four primary tests; secondary diagnostic p-values are descriptive and not additional confirmatory tests.','SmallX')

# 9 discussion
page();title('06 / Discussion & conclusion','Robust signals, bounded recommendations')
h('Sensitivity checks')
p('Removing 250,306 exact repeats in the OULAD early window leaves O1 OR=0.777 [0.742, 0.814] and O2 OR=0.910 [0.882, 0.939]. Restricting to Fail versus Pass/Distinction (n=8,285; exclude Withdrawn) also preserves both directions: OR=0.732 and 0.930. Thus the primary associations are not explained solely by repeated counts or withdrawal outcomes.')
p('In a fixed logistic ablation, volume/context plus submission features achieves AUROC 0.752; adding active days gives 0.766, adding momentum alone 0.754, and adding both 0.768. These secondary point estimates suggest that activity spread supplies most of the additional temporal discrimination; they are not separately significance-tested.')
table([['Moodle session gap','Sessions','Median minutes','Observed total hours'],['15 minutes','2,396','1.23','257.1'],['30 minutes','2,142','1.63','347.1'],['60 minutes','1,938','2.09','489.8']],[.28,.21,.24,.27])
p('Total observed session time changes by about 91% from a 15- to 60-minute gap. Time proxies therefore should not be treated as ground truth. The primary hypotheses and cluster inputs use counts and days, not duration. Retaining telemetry yields M1=+1.831 days and M2=-0.914 days; a bounded fractional-logit sensitivity also preserves their directions and support decisions.')
h('Implications for course design and support')
p('<b>Prioritize continuity:</b> offer small, recurring learning opportunities and optional planning prompts. Active-day spread is associated with both academic outcomes and later participation, even after volume adjustment. This motivates an intervention trial, not a claim that inducing extra LMS visits will improve learning.')
p('<b>Review sudden decline in context:</b> a tutor could compare recent weeks with the learner’s own history, check course-wide quiet periods, and offer help. The random forest’s 1,988 false positives make automated penalties inappropriate. Test AUROC also varies by module from 0.675 to 0.807; local validation is necessary before deployment.')
p('<b>Avoid one profile for every learner:</b> sparse users may need orientation, while quiz-focused users may need support connecting assessment to resources. These are hypotheses for co-designed support, not diagnosed deficits. The unsupported diversity hypothesis argues against setting resource-breadth targets solely from these logs.')
h('Limits and conclusion')
p('Results are observational, cohort-specific and conditioned on surviving/arriving before the cutoff. OULAD excludes unseen contexts and early withdrawals; Moodle has only 141 modeled IDs, unknown roles, no grades or verified course schedule, and just one recorded forum-post event. Offline learning and logging differences remain unmeasured. The strongest common finding is that <b>returning across days carries information beyond interaction volume</b>; causality and intervention benefit require prospective evaluation.')

# 10 references appendix
page();title('References & appendix','Sources and reproducibility')
refs=[
('[1]','Kuzilek, J., Hlosta, M., &amp; Zdrahal, Z. (2017). Open University Learning Analytics dataset. <i>Scientific Data, 4</i>, 170171.','https://doi.org/10.1038/sdata.2017.171'),
('[2]','OULAD: specified Kaggle mirror (anlgrbz), seven CSV tables. Official data dictionary and CC BY 4.0 licence: OU Analyse. Accessed 29 September 2026.','https://www.kaggle.com/datasets/anlgrbz/student-demographics-online-education-dataoulad'),
('[3]','Course-provided <i>MOODLE Data.csv</i>, 32,494,642 bytes. Export covers 23 October 2025-29 July 2026; accessed 29 September 2026. Restricted raw data retained locally.','https://drive.google.com/file/d/1A82KQ0eZURKcxucUX00agbdz1qatwOjc/view'),
('[4]','Barzagar Nazari, K., &amp; Ebersbach, M. (2018). Distributed Practice: Rarely Realized in Self-Regulated Mathematical Learning. <i>Frontiers in Psychology, 9</i>, 2170.','https://doi.org/10.3389/fpsyg.2018.02170'),
('[5]','Kovanovic, V., Gasevic, D., Dawson, S., Joksimovic, S., &amp; Baker, R. (2016; issue 2015). Does Time-on-task Estimation Matter? Implications on Validity of Learning Analytics Findings. <i>Journal of Learning Analytics, 2</i>(3), 81-110.','https://doi.org/10.18608/jla.2015.23.6'),
('[6]','Course supplementary interaction folder (61 task-log CSVs) and activity-artifact folder. Inspected for scope; not merged because their schema/identifiers are incompatible with [3].','https://drive.google.com/drive/folders/1CTmRImthvj1ZONzgJ5DEeoRcAv3kFQ-c')]
for lab,desc,url in refs:p(f'{lab} {desc} <link href="{escape(url)}" color="#176B87">Source link</link>.','SmallX')
p('Official OULAD field dictionary: <link href="https://research.stem.open.ac.uk/ouanalyse/open-dataset-more/" color="#176B87">OU Analyse documentation</link>. Supplementary artifact folder: <link href="https://drive.google.com/drive/folders/1aX5Ul_Bz7jelimgstsTmq02kqr5-JAfW" color="#176B87">course Drive</link>.','SmallX')
h('Appendix A. Executable code and audit trail')
p(f'<b>Public repository:</b> <link href="{REPO}" color="#176B87">{REPO}</link>')
table([['File','Purpose'],['src/download_data.py','Download the specified OULAD mirror; install an authorized local Moodle export.'],['src/analyze.py','Cleaning, feature construction, temporal charts, models, hypothesis tests and all primary aggregate results.'],['src/robustness.py','Deduplication, Fail-only, feature ablation and bounded-outcome sensitivity checks.'],['src/build_report.py; src/verify.py','Generate this PDF; verify counts, metric consistency, artifacts and the ten-page limit.'],['PROTOCOL.md; requirements.txt','Declared primary decisions, secondary diagnostics and pinned Python package versions.'],['results/; figures/','Machine-readable aggregate results, input SHA-256 checksums and figure outputs. No raw or learner-level records.']],[.36,.64])
p('<b>Reproduce:</b> create a Python 3.13 virtual environment; install requirements.txt; run download_data.py with --moodle pointing to the authorized course CSV; then run analyze.py, robustness.py, build_report.py and verify.py in that order. Random seed=610. Full commands are in the repository README. Access to the original Moodle export is required; it is not redistributed.')
p('The local raw-data hashes fix input identity. Assertion checks cover join uniqueness, disjoint people across OULAD splits, early/future separation and valid timestamps. Result tables drive the report metrics; metric and page checks plus visual inspection support delivery quality. AI assistance was used for coding, analysis and report preparation; the scripts and aggregate outputs make the computations inspectable.','SmallX')

doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=48,bottomMargin=44,title='Beyond click counts: Learning Behaviour Analytics',author='Darshan Sonawane; Aditya Singh; Ashok Kumar',subject='ET 610 group assignment: OULAD and Moodle')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
reader=PdfReader(out);print(f'Created {out} ({len(reader.pages)} pages)')
assert len(reader.pages)==10, f'Expected exactly ten pages, found {len(reader.pages)}'
