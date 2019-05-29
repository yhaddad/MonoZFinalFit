import yaml
import ROOT
import uproot
import os
import math
import argparse
import ftool
from pprint import pprint

ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gErrorIgnoreLevel=ROOT.kError

def main():
    parser = argparse.ArgumentParser(description='The Creator of Combinators')
    parser.add_argument("-i", "--input"   , type=str, default="config/inputs.yaml")
    parser.add_argument("-v", "--variable", type=str, default="measMET")
    parser.add_argument("-o", "--outdir"  , type=str, default="fitroom")
    parser.add_argument("-c", "--channel" , action="append")
    parser.add_argument("-s", "--signal"  , action="append")
    parser.add_argument("-t", "--stack"   , type=str)
    parser.add_argument("-tag", "--tag"   , type=str, default="DMSim")


    options = parser.parse_args()
    # create a working directory where to store the datacards
    try:
        os.mkdir(options.outdir)
        print("Directory " , options.outdir ,  " Created ")
    except FileExistsError:
        print("Directory " , options.outdir ,  " already exists")

    # read the input files that contains the shapes
    # this is produced by the MonoZWSproducer
    # make sure to run the nanohadd.py on lxplus to make these files
    inputs = None
    with open(options.input) as f:
        try:
            inputs = yaml.safe_load(f.read())
        except yaml.YAMLError as exc:
            print(exc)
    # make datasets per prcess
    # from the yaml, you have already decided to group the MC in a certain way
    # Somboday can try to do it as it was done in MonoZ2016
    datasets = {}
    options.stack = options.stack.split(",")
    for dg in options.stack:
        print (" -- data group : ", inputs[dg]["type"], dg)
        p = ftool.DataGroup(
            inputs[dg]["files"],
            ptype=inputs[dg]["type"],
            variable= options.variable,
            rebin=4 if (options.channel[0]=="3L" or options.channel[0] =="4L") else 1,
            proc=dg, luminosity=0.1
        )
        datasets[dg] = p

    if options.stack is None:
        options.stack = ["WW", "ZZ", "WZ", "DY", "TOP", "Data"]

    ws = ftool.Workspace("ws.root", working_dir=options.outdir)

    for ch in options.channel:
        def bin_name(hist, ibin):
            return "bin{}to{}".format(
                int(hist.GetXaxis().GetBinLowEdge(ibin + 1)),
                int(hist.GetXaxis().GetBinUpEdge (ibin + 1))
            )
        def addNuisance(card, nuisName, process, rate):
            if nuisName not in card["nuisances"]:
                card["nuisances"][nuisName] = {}
            card["nuisances"][nuisName][process] = rate

        shapeHistName = "%s_%s" % (ch, options.variable)
        data_obs = datasets.get("Data").shape(ch, "nom")
        print("data_obs -->", data_obs, ch)
        for ibin in range(data_obs.GetNbinsX()):
            channel = "%s_%s" % (ch, bin_name(data_obs, ibin))
            if ch in ['3L', '4L']:
                channel = "cat" + channel
            ws.addChannel(channel)
            card = ws.cards[channel]
            card["observation"].append("bin          %s" % channel)
            card["observation"].append("observation  %1.3f" % int(data_obs.GetBinContent(ibin+1)) )

        def addNominal(process):
            nominalHist = datasets.get(process).shape(ch, "nom")
            shapeName = "%s_%s" % (process, ch)
            ftool.checkShape(nominalHist, shapeName)
            for ibin in range(nominalHist.GetNbinsX()):
                channel = "%s_%s" % (ch, bin_name(nominalHist, ibin))
                if ch in ['3L', '4L']:
                    channel = "cat" + channel
                card = ws.cards[channel]
                b = nominalHist.GetBinContent(ibin + 1)
                card["rates"].append((process, b))
                e = nominalHist.GetBinError(ibin + 1)
                if math.isnan(b) or math.isnan(e):
                    print("Warning: NAN found in %s_%s (%.0f-%.0f)" % (
                        process, channel, nominalHist.GetXaxis().GetBinLowEdge(ibin + 1),
                        nominalHist.GetXaxis().GetBinUpEdge(ibin + 1)
                    ))
                    continue
                if b == 0.:
                    print("Warning: Zero bin in %s_%s (%.0f-%.0f)" % (
                        process, channel, nominalHist.GetXaxis().GetBinLowEdge(ibin + 1),
                        nominalHist.GetXaxis().GetBinUpEdge(ibin + 1)
                    ))
                else:
                    addNuisance(card, "McStat_%s_%s lnN" % (channel, process), process, 1.+e/b)

        def addShapeNuisance(process, nuisance, cardName):
            histUp, histDown = datasets.get(process).shape(ch, nuisance)
            nominalHist = datasets.get(process).shape(ch, "nom")

            hupratio = histUp.Clone("tmpratio1")
            hupratio.Divide(nominalHist)
            hdownratio = histDown.Clone("tmpratio2")
            hdownratio.Divide(nominalHist)

            shapeName = "%s_%s_%sUp" % (process, ch, cardName)
            ftool.checkShape(histUp, shapeName)
            shapeName = "%s_%s_%sDown" % (process, ch, cardName)
            ftool.checkShape(histDown, shapeName)
            for iBin in range(histUp.GetNbinsX()):
                channel = "%s_%s" % (ch, bin_name(nominalHist, iBin))
                if ch in ['3L', '4L']:
                    channel = "cat" + channel
                card = ws.cards[channel]
                upR = hupratio.GetBinContent(iBin + 1)
                if upR <= 0.:
                  upR = 0.1
                downR = hdownratio.GetBinContent(iBin + 1)
                if downR <= 0.:
                  downR = 0.1
                addNuisance(card, "%s lnN" % cardName, process, (upR, downR))

        for p, pg in  datasets.items():
            if 'data'   in pg.ptype: continue
            #if 'signal' in pg.ptype: continue
            addNominal(p)
            # we need to add more systematics here
            addShapeNuisance(p, "ElectronEn", "CMS_Scale_el")
            addShapeNuisance(p, "MuonEn"    , "CMS_Scale_mu")
            addShapeNuisance(p, "MuonSF"    , "CMS_Eff_mu")
            addShapeNuisance(p, "jesTotal"  , "CMS_JES")
            addShapeNuisance(p, "jer"       , "CMS_JER")
            addShapeNuisance(p, "unclustEn" , "CMS_UES")
            addShapeNuisance(p, "puWeight"  , "CMS_Scale_pileup")
            for iBin in range(data_obs.GetNbinsX()):
                bn = bin_name(data_obs, iBin)
                channel = "%s_%s" % (ch, bn)
                if ch in ['3L', '4L']:
                    channel = "cat" + channel
                card = ws.cards[channel]
                addNuisance(card, "CMS_lumi_2017 lnN", p, 1.026)

        # Uncorrelated theory uncertainties in signal and main backgrounds
        theory_bkgs = []
        signalGroup = [ c for i, c in datasets.items() if c.ptype=="signal"]
        if ch in ['EE', 'MM', '2L', '3L']:
            theory_bkgs.append(datasets.get("WZ3lnu"))
        if ch in ['EE', 'MM', 'NRB']:
            theory_bkgs.append(datasets.get("qqZZ2l2nu"))
        if ch in ['4L']:
            theory_bkgs.append(datasets.get("qqZZ4l"))

        print("signals : ", signalGroup)
        for pg in theory_bkgs + signalGroup:
            process = pg.proc
            print("-----:: ", process)
            if 'DM' in process or 'ADD' in process:
                for iBin in range(data_obs.GetNbinsX()):
                    bn = bin_name(data_obs, iBin)
                    channel = "%s_%s" % (ch, bn)
                    if ch in ['3L', '4L']:
                        channel = "cat" + channel
                    card = ws.cards[channel]
                    addNuisance(card, "Theo_pdfAlphaS_%s lnN" % process, process, 1.01)
                    addNuisance(card, "Theo_factRenormScale_%s lnN" % process, process, 1.05)
            # this now commented as it is not yet implemented in our code
            #if process in ['WZ3lnu', 'qqZZ2l2nu', 'qqZZ4l']:
            #    addShapeNuisance(process, "factRenormScale", "Theo_factRenormScale_VV")
            #else:
            #    addShapeNuisance(process, "factRenormScale", "Theo_factRenormScale_%s" % process)
        print("")
        for iBin in range(data_obs.GetNbinsX()):
            bn = bin_name(data_obs, iBin)
            channel = "%s_%s" % (ch, bn)
            if ch in ['3L', '4L']:
                channel = "cat" + channel
            card = ws.cards[channel]

            if ch == 'EE':
                card["extras"].add("NRBnorm_ReSquared rateParam ee* Nonresonant 1 [0.01,10]")
                # if not args.noNRBinflate:
                #     addNuisance(card, "NRBnorm_Inflate lnN", "Nonresonant", 1.2)
            elif ch == 'MM':
                card["extras"].add("NRBnorm_RmSquared rateParam mm* Nonresonant 1 [0.01,10]")
                # if not args.noNRBinflate:
                #     addNuisance(card, "NRBnorm_Inflate lnN", "Nonresonant", 1.2)
            elif ch == 'NRB':
                card["extras"].add("NRBnorm_RmSquared rateParam ll* Nonresonant 1 [0.01,10]")
                card["extras"].add("NRBnorm_ReSquared rateParam ll* Nonresonant @0 NRBnorm_RmSquared")
                addNuisance(card, "NRBnorm_Inflate lnN", "Nonresonant", 1.2)
            elif ch == 'EM':
                card["extras"].add("NRBnorm_ReRm rateParam em* Nonresonant sqrt(@0*@1) NRBnorm_ReSquared,NRBnorm_RmSquared")

            vvNormName = "allBins"

            if ch in ['EE', 'MM', 'NRB']:
                if bn != 'bin50to100':
                    card["extras"].add("ZZWZNorm_%s rateParam %s_%s qqZZ2l2nu 1. [0.01,10]" % (vvNormName, ch, bn))
                    card["extras"].add("ZZWZNorm_%s rateParam %s_%s ggZZ2l2nu 1. [0.01,10]" % (vvNormName, ch, bn))
                    card["extras"].add("ZZWZNorm_%s rateParam %s_%s WZ3lnu 1. [0.01,10]" % (vvNormName, ch, bn))
                    addNuisance(card, "CMS_InflateDY2lNorm lnN", "DrellYan", 2.)
                card["extras"].add("DrellYanNorm rateParam %s_%s DrellYan 1. [0.01,10]" % (ch, bn))
            elif ch in ['EE', 'MM', 'NRB']:
                addNuisance(card, "CMS_NonPromptLepWZinSR lnN", "WZ3lnu", 1.03)
            elif ch == '3L':
                card["extras"].add("ZZWZNorm_%s rateParam %s_%s WZ3lnu 1. [0.01,10]" % (vvNormName, ch, bn))
                addNuisance(card, "CMS_NonPromptLepDYinWZ lnN", "NonPromptDY", 1.3)
            elif ch == '4L':
                card["extras"].add("ZZWZNorm_%s rateParam %s_%s qqZZ4l 1. [0.01,10]" % (vvNormName, ch, bn))
                card["extras"].add("ZZWZNorm_%s rateParam %s_%s ggZZ4l 1. [0.01,10]" % (vvNormName, ch, bn))
                addNuisance(card, "CMS_InflateOther4lNorm lnN", "Other4l", 1.4)


    ws.write(makeGroups=False)



if __name__ == "__main__":
    main()
