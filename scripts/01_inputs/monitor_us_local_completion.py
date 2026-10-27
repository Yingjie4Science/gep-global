"""Monitor the authorized acquisition; perform bounded retry and final local audits.

Run in the geospatial model environment, with GEP_DOWNLOAD_TRANSPORT=curl.
No scheduler or service is installed; this process must remain running.
"""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path

def alive(pid):
 try:os.kill(pid,0);return True
 except ProcessLookupError:return False

def main():
 p=argparse.ArgumentParser();p.add_argument('data_root',type=Path);p.add_argument('--download-pid',type=int,required=True);p.add_argument('--retry-passes',type=int,default=1);a=p.parse_args();repo=Path(__file__).resolve().parents[2];status=a.data_root/'manifests/us_local_completion.json';plan=json.loads((a.data_root/'manifests/glc_us_download_plan.json').read_text())['tiles'];record={'status':'acquiring','expected_tiles':len(plan),'retry_passes':0};pid=a.download_pid;child=None
 def save():
  record['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();temp=status.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(status)
 while True:
  verified=sum((a.data_root/'manifests/glc_us_tiles'/(Path(t['member']).name+'.json')).exists() and json.loads((a.data_root/'manifests/glc_us_tiles'/(Path(t['member']).name+'.json')).read_text()).get('status')=='verified' for t in plan)
  record['verified_tiles']=verified;save()
  if verified==len(plan):break
  running=child.poll() is None if child else alive(pid)
  if not running:
   if record['retry_passes']>=a.retry_passes:record.update(status='acquisition_incomplete',reason='Bounded acquisition retries exhausted; inspect failed tile manifests');save();return
   record['retry_passes']+=1
   log=(a.data_root/'manifests/glc_resume.log').open('a')
   child=subprocess.Popen([sys.executable,str(repo/'scripts/01_inputs/fetch_glc_fcs30d_us.py'),str(a.data_root),'--workers','3'],stdout=log,stderr=subprocess.STDOUT,cwd=repo)
  time.sleep(30)
 out=a.data_root/'manifests/us_local_qc_2019_v1';out.mkdir(exist_ok=True)
 for stage,command in [('acquisition_audit',[sys.executable,repo/'scripts/03_checks/verify_land_cover_acquisition.py',a.data_root,out/'acquisition_audit.json']),('national_coverage_audit',[sys.executable,repo/'scripts/03_checks/check_us_land_cover_coverage.py',a.data_root,out])]:
  record['status']=stage;save();subprocess.run([str(x) for x in command],check=True,cwd=repo)
 audit=json.loads((out/'acquisition_audit.json').read_text());coverage=json.loads((out/'coverage_summary.json').read_text());record.update(acquisition_audit_passed=audit['complete'],cities_with_missing_support=coverage['cities_with_missing_support'])
 if not audit['complete']:record['status']='audit_failed';save();return
 record['status']='waiting_expanded_tests';save();root=a.data_root/'outputs/sf_minneapolis_2019_v1'
 while True:
  cities=json.loads((root/'test_plan.json').read_text())['cities'];completed=[c['label'] for c in cities if (root/c['label']/'comparison.json').exists()];failures=[c['label'] for c in cities if (root/c['label']/'failure.json').exists() and c['label'] not in completed];record['completed_city_tests']=completed;record['failed_city_tests']=failures;save()
  if failures:record['status']='expanded_test_failed';save();return
  if len(completed)==len(cities):break
  time.sleep(30)
 record['status']='complete_with_coverage_findings' if coverage['cities_with_missing_support'] else 'complete';save();print(json.dumps(record),flush=True)
if __name__=='__main__':main()
