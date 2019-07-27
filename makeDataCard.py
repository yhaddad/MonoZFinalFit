import yaml
import ROOT
import uproot
import os
import math
import argparse
import ftool
from termcolor import colored
from pprint import pprint

ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gErrorIgnoreLevel=ROOT.kError

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
    parser.add_argument("-c"  , "--channel" , action="append")
    parser.add_argument("-s"  , "--signal"  , action="append")
    parser.add_argument("-t"  , "--stack"   , type=str)
    parser.add_argument("-era", "--era"     , type=str, default="2017")
    parser.add_argument("-f"  , "--force"   , action="store_true")
    parser.add_argument("-tag", "--tag"     , type=str, default="ADD")
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
            print "Directory " , options.outdir ,  " Re-created "

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

    # make datasets per prcess
    datasets = {}
    options.stack = options.stack.split(",")
    nsignals = 0
    for dg in options.stack:
        p = ftool.DataGroup(
            inputs[dg]["files"],
            ptype      = inputs[dg]["type"],
            variable   = options.variable,
            rebin      = 1,
            proc       = dg,
            kfactor    = inputs[dg].get("kfactor", 1.0),
            xsections  = xsections,
            luminosity = lumis[options.era]
        )
        if inputs[dg]["type"].lower() == "signal":
            p.save(
                filename="histogram-{}.root".format("DM"),
                working_dir=options.outdir
            )
        else:
            p.save(
                filename="histogram-{}.root".format(dg),
                working_dir=options.outdir
            )
        if inputs[dg]["type"].lower() =='signal':
            nsignals += 1

        print colored(" -- data group : " + inputs[dg]["type"] + " : " + dg, "green")
        if 'signal' in inputs[dg]["type"]:
            dg = dg.replace(dg, "DM")
        # ---
        datasets[dg] = p

    if options.stack is None:
        options.stack = ["WW", "ZZ", "WZ", "DY", "TOP", "Data"]

    ws = ftool.DataCard("ws.root", working_dir=options.outdir)
    ws.nSignals = nsignals

    for ch in options.channel:
        if "catSignal-0jet" in ch:
            ch = ch.replace("catSignal-0jet", "BSM0")
        if "catSignal-1jet" in ch:
            ch = ch.replace("catSignal-1jet", "BSM1")

        data_obs = datasets.get("Data").shape(ch, "nom")
        ftool.checkShape(data_obs, "data{}".format(ch))

        ws.addChannel(ch)
        ws.cards[ch]["observation"].append("bin          {}".format(ch))
        ws.cards[ch]["observation"].append("observation  {}".format(data_obs.Integral()))

        ws.cards[ch]["shapes"].append(
            "shapes {process:<20} {channel:<10} {file:>20} {variable}_{proc}_{channel}".format(
                process="data_obs",
                proc="data",
                channel=ch,
                file="histogram-Data.root",
                variable=options.variable
            )
        )


        def add_nuisance(nuisName, process, rate):
            if nuisName not in ws.cards[ch]["nuisances"]:
                ws.cards[ch]["nuisances"][nuisName] = {}
            ws.cards[ch]["nuisances"][nuisName][process] = rate

        def add_nominal(process):
            nominalHist = datasets.get(process).shape(ch, "nom")
            ftool.checkShape(nominalHist, "{}_{}".format(process, ch))
            ws.cards[ch]["rates" ].append((process, nominalHist.Integral()))
            ws.cards[ch]["shapes"].append(
                "shapes {process:<20} {channel:<10} {file:>20} {variable}_{process}_{channel}_$SYSTEMATIC".format(
                    process=process, channel=ch,
                    file="histogram-{}.root".format(process),
                    variable=options.variable
                )
            )
            #ws.cards[ch]["extras"].add("{:<10} autoMCStats 0 0 1".format(process))

        def add_shape_nuisance(process, nuisance, cardName):
            print "process : ", process, " : ", nuisance
            histUp, histDown = datasets.get(process).shape(ch, nuisance)
            print " -- > get proc : ", datasets.keys()
            nominalHist = datasets.get(process).shape(ch, "nom")

            try:
                def allBins(hist):
                    return [hist.GetBinContent(i + 1) for i in range(hist.GetNbinsX())]
                if allBins(histUp) == allBins(histDown):
                    print "Info: shape nuisance %s has no variation for process %s, skipping" % (nuisance, process)
                    return
            except:
                return


            nuisName = "{:<20} shape".format(cardName)
            add_nuisance(nuisName, process, 1.)

        for p, pg in  datasets.items():
            if 'data'   in pg.ptype: continue
            add_nominal(p)
            add_nuisance("CMS_Scale_el lnN", p, 1.02)
            add_nuisance("CMS_Scale_mu lnN", p, 1.01)

            if options.era == "2016":
                add_nuisance("CMS_lumi_2016 lnN".format(options.era), p, 1.025)
            if options.era == "2017":
                add_nuisance("CMS_lumi_2017 lnN".format(options.era), p, 1.023)
            if options.era == "2018":
                add_nuisance("CMS_lumi_2018 lnN".format(options.era), p, 1.025)
            add_nuisance("CMS_EUPS      lnN".format(options.era), p, 1.02)
            # -- objects
            add_shape_nuisance(p, "ElectronEn", "CMS_res_e")
            add_shape_nuisance(p, "ElecronSF" , "CMS_eff_e")
            add_shape_nuisance(p, "MuonEn"    , "CMS_res_m")
            add_shape_nuisance(p, "MuonSF"    , "CMS_eff_m")
            # -- jets/met
            add_shape_nuisance(p, "jesTotal"  , "CMS_JES_{}".format(options.era))
            add_shape_nuisance(p, "jer"       , "CMS_JER_{}".format(options.era))
            add_shape_nuisance(p, "unclustEn" , "CMS_UES_{}".format(options.era))
            # -- trigger and bjets
            add_shape_nuisance(p, "btagEventWeight", "CMS_BTag_{}".format(options.era))
            add_shape_nuisance(p, "TriggerSFWeight", "CMS_Trig_{}".format(options.era))
            add_shape_nuisance(p, "PrefireWeight"  , "CMS_Prefire_{}".format(options.era))
            # -- thoery uncert
            add_shape_nuisance(p, "EWK"  , "EWKZZWZ")
            add_shape_nuisance(p, "PDF"  , "PDF")
            # -- pu/vtx reweighting
            add_shape_nuisance(p, "nvtxWeight", "CMS_Vx")
            add_shape_nuisance(p, "puWeight"  , "CMS_PU")

    ws.write(makeGroups=False)



if __name__ == "__main__":
    main()
