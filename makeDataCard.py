import yaml
import uproot
import os
import argparse
import ftool
import numpy as np
from termcolor import colored


lumis = {
    "2016" : 35.9,
    "2017" : 41.5,
    "2018" : 60.0
}

def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-i"  , "--input"   , type=str, default="config/inputs.yaml")
    parser.add_argument("-v"  , "--variable", type=str, default="measMET")
    parser.add_argument("-o"  , "--outdir"  , type=str, default="fitroom")
    parser.add_argument("-c"  , "--channel" , nargs='+', type=str)
    parser.add_argument("-s"  , "--signal"  , nargs='+', type=str)
    parser.add_argument("-t"  , "--stack"   , nargs='+', type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-xs" , "--xsection", type=str, default="config/xsections_2017.yaml")

    options = parser.parse_args()
    # create a working directory where to store the datacards
    try:
        os.mkdir(options.outdir)
        print("Directory " , options.outdir ,  " Created ")
    except:
        if options.force:
            os.rmdir(options.outdir)
            os.mkdir(options.outdir)
            print("Directory " , options.outdir ,  " Re-created ")

    inputs = None
    with open(options.input) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    xsections = None
    with open(options.xsection) as f:
        try:
            xsections = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)

    if len(options.channel) == 1:
        options.channel = options.channel[0]

    # make datasets per prcess
    datasets = {}
    nsignals = 0
    signal = ""
    for dg in options.stack:
        p = ftool.datagroup(
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"],
            observable = options.variable,
            name       = dg,
            kfactor    = inputs[dg].get("kfactor", 1.0),
            xsections  = xsections,
            channel    = options.channel, #["cat3L", "cat4L", "catEM", "catSignal-0jet", "catSignal-1jet"],
            luminosity = lumis[options.era]
        )
        #p.save()
        datasets[p.name] = p
        if p.ptype == "signal":
            signal = p.name

    print ("channel  : ", options.channel)

    card_name = "ch"+options.era
    if isinstance(options.channel, str):
        card_name = options.channel+options.era
    elif isinstance(options.channel, list):
        if np.all(["signal" in c.lower() for c in options.channel]):
            card_name = "chBSM"+options.era
    print(" -- cardname : ", card_name)

    card = ftool.datacard(
        name = signal,
        channel= card_name
    )
    card.shapes_headers()

    data_obs = datasets.get("data").get("nom")
    print("data_osb : ", data_obs)
    card.add_observation(data_obs)

    for n, p in datasets.items():
        name = "signal" if p.ptype=="signal" else p.name
        if p.ptype=="data":
            continue
        card.add_nominal(name, p.get("nom"))

        card.add_nuisance(name, "{:<21}  lnN".format("CMS_Scale_el"),  1.020)
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_Scale_mu"),  1.010)
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_2016"),  1.025)
        card.add_nuisance(name, "{:<21}  lnN".format("UEPS"),  1.020)
        #
        card.add_shape_nuisance(name, "ElectronEn", "CMS_res_e", p.get("ElectronEn"))
        card.add_shape_nuisance(name, "ElecronSF" , "CMS_eff_e", p.get("ElecronSF"))
        card.add_shape_nuisance(name, "MuonEn"    , "CMS_res_m", p.get("MuonEn"))
        card.add_shape_nuisance(name, "MuonSF"    , "CMS_eff_m", p.get("MuonSF"))
        #
        card.add_shape_nuisance(name, "jesTotal"  , "CMS_JES_2017", p.get("jesTotal"))
        card.add_shape_nuisance(name, "jer"       , "CMS_JER_2017", p.get("jer"))
        card.add_shape_nuisance(name, "unclustEn" , "CMS_UES_2017", p.get("unclustEn"))
        #
        card.add_shape_nuisance(name, "btagEventWeight" , "CMS_BTag_2017" , p.get("btagEventWeight"))
        card.add_shape_nuisance(name, "TriggerSFWeight" , "CMS_Trig_2017" , p.get("TriggerSFWeight"))
        card.add_shape_nuisance(name, "PrefireWeight"   , "CMS_pfire_2017", p.get("PrefireWeight"))
        #
        card.add_shape_nuisance(name, "EWK"  , "EWKZZWZ", p.get("EWK"))
        card.add_shape_nuisance(name, "PDF"  , "PDF"    , p.get("PDF"))
        #
        card.add_shape_nuisance(name, "nvtxWeight", "CMS_Vx", p.get("nvtxWeight"))
        card.add_shape_nuisance(name, "puWeight"  , "CMS_PU", p.get("puWeight"))
        #
        card.add_auto_stat()

    card.dump()


if __name__ == "__main__":
    main()
