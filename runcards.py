import yaml
import glob
import os
import multiprocessing
import subprocess
import shlex


options_input = "config/inputs-NanoAODv5-{}.yaml"

from multiprocessing.pool import ThreadPool

def call_makeDataCard(cmd):
    """ This runs in a separate thread. """
    print(" ---- [%] :", cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)


pool = ThreadPool(multiprocessing.cpu_count())
results = []
for year in [2017]:
    with open(options_input.format(year)) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print ("failed to open the YAML ....")
            print (exc)
    for n, sam in inputs.items():
        if "ADD_MD_1_d_2" not in n: continue
        print(" ===== processing : ", n, sam, year)
        cmd_sr = "python3 makeDataCard.py --channel catSignal-0jet catSignal-1jet "
        cmd_sr += "--variable MT " if "2HDM" in n else "" 
        cmd_sr += "--stack {signal} ZZ WZ WW VVV TOP DY data "
        cmd_sr += "--input=config/inputs-NanoAODv5-{era}.yaml --era={era}"
        cmd_sr = cmd_sr.format(signal=n, era=year)
        
        cmd_3l = "python3 makeDataCard.py --channel cat3L "
        cmd_3l += "--stack {signal} ZZ WZ WW VVV TOP DY data --binrange 1 20 "
        cmd_3l += "--input=config/inputs-NanoAODv5-{era}.yaml --era={era}"
        cmd_3l = cmd_3l.format(signal=n, era=year)
        
        cmd_4l = "python3 makeDataCard.py --channel cat4L "
        cmd_4l += "--stack {signal} ZZ WZ WW VVV TOP DY data --binrange 1 20 "
        cmd_4l += "--input=config/inputs-NanoAODv5-{era}.yaml --era={era}"
        cmd_4l = cmd_4l.format(signal=n, era=year)
        
        cmd_em = "python3 makeDataCard.py --channel catEM "
        cmd_em += "--stack {signal} ZZ WZ WW VVV TOP DY data --binrange 1 20 --rebin=4 "
        cmd_em += "--input=config/inputs-NanoAODv5-{era}.yaml --era={era}"
        cmd_em = cmd_em.format(signal=n, era=year)
        
        results.append(pool.apply_async(call_makeDataCard, (cmd_sr,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_3l,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_4l,)))
        results.append(pool.apply_async(call_makeDataCard, (cmd_em,)))

# Close the pool and wait for each running task to complete
pool.close()
pool.join()
for result in results:
    out, err = result.get()
    #print("out: {}".format(out))
    if "No such file or directory" in str(err):
        print(str(err))
        print(" ----------------- ")
        print()