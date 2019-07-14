import os

indir = "/eos/cms/store/group/phys_exotica/monoZ/LionKing2017"
outdir = "/eos/cms/store/group/phys_exotica/monoZ/LionKing2017/merged2017"

for sample in os.listdir(indir):
    print sample
    command = "./haddnano.py {outdir}/{sample}.root {indir}/{sample}/*.root".format(
                sample = sample,
                outdir = outdir,
                indir  = indir
            )
    os.system(command)
