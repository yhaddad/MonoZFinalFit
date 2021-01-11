import os
import glob
import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex

combine_options = " --rMin=0, --cminFallbackAlgo Minuit2,Migrad,0:0.05  --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH"

dcards = glob.glob("cards-*")


def call_combine(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (out, err)

pool = ThreadPool(multiprocessing.cpu_count())
results = []

for dc in dcards:
    print(" -- making :", dc)
    name= dc.replace("cards-", "")
    if "2HDM" not in name:
        continue
    print(" --- name : ", name)
    os.system("rm -rf cards-{}/combined.dat".format(name))
    os.system(
            "combineCards.py -S "
            "cat3L2016=cards-{name}/shapes-cat3L2016.dat "
            "cat4L2016=cards-{name}/shapes-cat4L2016.dat "
            "chBSM2016=cards-{name}/shapes-chBSM2016.dat "
            "catEM2016=cards-{name}/shapes-catEM2016.dat "
            "cat3L2017=cards-{name}/shapes-cat3L2017.dat "
            "cat4L2017=cards-{name}/shapes-cat4L2017.dat "
            "chBSM2017=cards-{name}/shapes-chBSM2017.dat "
            "catEM2017=cards-{name}/shapes-catEM2017.dat "
            "cat3L2018=cards-{name}/shapes-cat3L2018.dat "
            "cat4L2018=cards-{name}/shapes-cat4L2018.dat "
            "chBSM2018=cards-{name}/shapes-chBSM2018.dat "
            "catEM2018=cards-{name}/shapes-catEM2018.dat "
            "> cards-{name}/combined.dat".format(name=name))
    os.system("text2workspace.py -m 125 cards-{name}/combined.dat -o cards-{name}/combined.root".format(name=name))
    command = (
        "combine "
        " -M AsymptoticLimits --datacard cards-{name}/combined.root"
        #" -M FitDiagnostics -datacard cards-{name}/combined.root --plots signalPdfNames='ADD*,Signal' --backgroundPdfNames='*DY*,*WW*,*TOP*,ZZ*,WZ*,VVV'"
        " -m 125 --name {name} {options}"
        ##" --rMin=0 --cminFallbackAlgo Minuit2,Migrad,0:0.05"
        " --X-rtd MINIMIZER_analytic --X-rtd FAST_VERTICAL_MORPH".format(
            name=name,
            options="" #"--rMax=10" if "ADD" in name else "--rMax=10"
        )
    )
    results.append(pool.apply_async(call_combine, (command,)))

pool.close()
pool.join()

for result in results:
    out, err = result.get()
    if "error" in str(err).lower():
        print(str(err))
        print(" ----------------- ")
        print()
