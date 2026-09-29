"""Download public OULAD and install an authorized local Moodle export."""
import argparse, shutil, zipfile
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--moodle',type=Path,help='Path to MOODLE Data.csv downloaded from the course Drive');args=p.parse_args()
raw=ROOT/'data/raw';(raw/'oulad').mkdir(parents=True,exist_ok=True);(raw/'moodle').mkdir(exist_ok=True)
url='https://www.kaggle.com/api/v1/datasets/download/anlgrbz/student-demographics-online-education-dataoulad'
if not (raw/'oulad/studentVle.csv').exists():
 with requests.get(url,stream=True,timeout=180) as r:
  r.raise_for_status()
  with (raw/'oulad.zip').open('wb') as f:
   for chunk in r.iter_content(1024*1024):f.write(chunk)
 with zipfile.ZipFile(raw/'oulad.zip') as z:
  expected={'assessments.csv','courses.csv','studentAssessment.csv','studentInfo.csv','studentRegistration.csv','studentVle.csv','vle.csv'}
  assert expected.issubset(z.namelist()),'Unexpected OULAD archive'
  for name in expected:
   with z.open(name) as src,(raw/'oulad'/name).open('wb') as dst:shutil.copyfileobj(src,dst)
if args.moodle:
 target=raw/'moodle/moodle.csv'
 if args.moodle.resolve()!=target.resolve():shutil.copyfile(args.moodle,target)
if not (raw/'moodle/moodle.csv').exists():
 print('Download the authorized course export from https://drive.google.com/file/d/1A82KQ0eZURKcxucUX00agbdz1qatwOjc/view')
 print('Then rerun with --moodle "/path/to/MOODLE Data.csv". Moodle is not redistributed.')
else:print('Both datasets are ready. Run python src/analyze.py')
