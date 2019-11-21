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

lumi_unc = {
    "2016" : 1.025,
    "2017" : 1.023,
    "2018" : 1.025
}
def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-i"  , "--input"   , type=str, default="config/inputs-NanoAODv5-2018.yaml")
    parser.add_argument("-v"  , "--variable", type=str, default="measMET")
    parser.add_argument("-o"  , "--outdir"  , type=str, default="fitroom")
    parser.add_argument("-c"  , "--channel" , nargs='+', type=str)
    parser.add_argument("-s"  , "--signal"  , nargs='+', type=str)
    parser.add_argument("-t"  , "--stack"   , nargs='+', type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-xs" , "--xsection", type=str, default="config/xsections_ERA.yaml")
    parser.add_argument("--onexsec", action="store_true")

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
    with open(options.xsection.replace("ERA", options.era)) as f:
        print(" -- cross section file : ", options.xsection.replace("ERA", options.era))
        try:
            xsections = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print (exc)
    if options.onexsec:
        xsections = { s: {'br': 1.0, 'kr': 1.0, 'xsec': 1.0} for s, xs in xsections.items()}

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

    card_name = "ch"+options.era
    if isinstance(options.channel, str):
        card_name = options.channel+options.era
    elif isinstance(options.channel, list):
        if np.all(["signal" in c.lower() for c in options.channel]):
            card_name = "chBSM"+options.era

    card = ftool.datacard(
        name = signal,
        channel= card_name
    )
    card.shapes_headers()

    data_obs = datasets.get("data").get("nom")
    card.add_observation(data_obs)

    for n, p in datasets.items():
        name = "Signal" if p.ptype=="signal" else p.name
        if p.ptype=="data":
            continue
        card.add_nominal(name, p.get("nom"))
        #
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_Scale_el"),  1.020)
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_Scale_mu"),  1.010)
        card.add_nuisance(name, "{:<21}  lnN".format("CMS_lumi_{}".format(options.era)),  lumi_unc[options.era])
        card.add_nuisance(name, "{:<21}  lnN".format("UEPS"),  1.020)
        #
        card.add_shape_nuisance(name, "ElectronEn", "CMS_res_e", p.get("ElectronEn"))
        card.add_shape_nuisance(name, "ElecronSF" , "CMS_eff_e", p.get("ElecronSF"))
        card.add_shape_nuisance(name, "MuonEn"    , "CMS_res_m", p.get("MuonEn"))
        card.add_shape_nuisance(name, "MuonSF"    , "CMS_eff_m", p.get("MuonSF"))
        #
        card.add_shape_nuisance(name, "jesTotal"  , "CMS_JES_{}".format(options.era), p.get("jesTotal"))
        card.add_shape_nuisance(name, "jer"       , "CMS_JER_{}".format(options.era), p.get("jer"))
        card.add_shape_nuisance(name, "unclustEn" , "CMS_UES_{}".format(options.era), p.get("unclustEn"))
        #
        card.add_shape_nuisance(name, "btagEventWeight" , "CMS_BTag_{}".format(options.era) , p.get("btagEventWeight"))
        card.add_shape_nuisance(name, "TriggerSFWeight" , "CMS_Trig_{}".format(options.era) , p.get("TriggerSFWeight"))
        if options.era in ['2016','2017']:
            card.add_shape_nuisance(name, "PrefireWeight"   , "CMS_pfire_{}".format(options.era), p.get("PrefireWeight"))
        #
        #if name in ["ZZ", "WZ"]:
        #    card.add_shape_nuisance(name, "EWK"  , "EWKZZWZ", p.get("EWK"))
        if name in ["ZZ"]:
            card.add_shape_nuisance(name, "EWK"  , "EWKZZ", p.get("EWK"))
        if name in ["WZ"]:
            card.add_shape_nuisance(name, "EWK"  , "EWKWZ", p.get("EWK"))
        card.add_shape_nuisance(name, "PDF"  , "PDF"    , p.get("PDF"))
        #
        card.add_shape_nuisance(name, "nvtxWeight", "CMS_Vtx", p.get("nvtxWeight"))
        card.add_shape_nuisance(name, "puWeight"  , "CMS_PU", p.get("puWeight"))

        #card.add_shape_nuisance(name, "QCDScale0w"  , "CMS_QCDScale0"    , p.get("QCDScale0w"))
        #card.add_shape_nuisance(name, "QCDScale1w"  , "CMS_QCDScale1"    , p.get("QCDScale1w"))
        #card.add_shape_nuisance(name, "QCDScale2w"  , "CMS_QCDScale2"    , p.get("QCDScale2w"))
        # define rates
        if name  in ["WW", "TOP"]:
            if "catEM" in card_name:
                card.add_rate_param("EMnorm_" + options.era, "catEM*", name)
            elif "BSM" in card_name:
                card.add_rate_param("EMnorm_" + options.era, "chBSM*", name)
                #card.add_nuisance(name, "{:<21}  lnN".format("EMNorm"+name),  1.2)
        elif name in ["ZZ", "WZ"]:
            if ("cat3L" in card_name) or ("cat4L" in card_name):
                card.add_rate_param("VVnorm_" + options.era, "cat3L*", name)
                card.add_rate_param("VVnorm_" + options.era, "cat4L*", name)
            elif "BSM" in card_name:
                card.add_rate_param("VVnorm_" + options.era, "chBSM*", name)
                card.add_rate_param("VVnorm_" + options.era, "chBSM*", name)
                #card.add_nuisance(name, "{:<21}  lnN".format("VVNorm"+card_name),  1.2)
        elif name in ["DY"]:
            if  "BSM" in card_name:
                card.add_rate_param("DYnorm_" + options.era, "chBSM*", name)
                #card.add_nuisance(name, "{:<21}  lnN".format("CMS_DYNorm"+card_name),  1.2)

        card.add_auto_stat()
    card.dump()


if __name__ == "__main__":
    main()
